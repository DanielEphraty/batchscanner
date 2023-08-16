""" Class SikCli for low-level management of a CLI SSH session to a Siklu radio """
from importlib import resources
import ipaddress
import logging
import os
import paramiko
import re
import socket
import time
import tomllib

CONFIG_FILENM = 'sikssh_config.toml'  # Constants text_to_parse


class SikCli:
    """ An wrapper class for managing a CLI session with a Siklu radio:

        * Connect as an SSH client and open a virtual terminal
        * Derive the SSH banner and CLI prompt
        * Derive some basic key attributes (e.g., model)
        * Method to send a command and return the output
        * Method to tunnel into a responder (applicable for TG radios only)
        * Logging of program interaction with radio.

        SikSSH makes use of built-in parameters, most relating to low-level transport and logging.
        Parameters can be overriden by specifying new values in file *sikssh_config.toml*.
        For example::

            Example contents of file *sikssh_config.toml*
            ---------------------------------------------
            tcp_timeout = 5
            banner_timeout = 4
            ...

        Here is the list of all parameters and their default values:

        ==================  ==========  =====================================================================
        Constant            Defaults     Meaning
        ==================  ==========  =====================================================================
        tcp_timeout         5.5         Timemout [sec] for the TCP connection
        banner_timeout      4           Timeout [sec] to wait for the server to send the SSH banner
        auth_timeout        6           Timeout [sec] to wait for an authentication response from the server
        rw_timeout          1           Timeout [sec] on blocking read/write
        response_timeout    1           Timeout [sec] for radio to response to a command
        many                9999999     Max size of read buffer
        prompt_retries      5           The number of times to attempt and get the CLI prompt
        terminal_height     5000        Number of rows in VT100 terminal
        log_enable          True        Enable/disable logging
        log_dir             'ssh_logs'  Directory for log files (will be created if necessary)
        log_level_console   'CRITICAL'  Console logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_level_file      'INFO'      File logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        ==================  ==========  =====================================================================
    """

    # Parse TOML config file and override default parameters
    _params = {}
    try:
        _params = tomllib.loads(resources.files('batchscanner').joinpath(CONFIG_FILENM).read_text())
    except FileNotFoundError:
        print(f"SikCli: Using default program parameters: file '{CONFIG_FILENM}' not found")
    except tomllib.TOMLDecodeError as e:
        print(f"Using default program parameters: invalid TOML syntax in '{CONFIG_FILENM}':\n{e}")
    finally:
        tcp_timeout = _params.get('tcp_timeout', 5.5)  # Timemout [sec] for the TCP connection
        banner_timeout = _params.get('banner_timeout', 4)  # Timeout [sec] to wait for the server to send the SSH banner
        auth_timeout = _params.get('auth_timeout',
                                   6)  # Timeout [sec] to wait for an authentication response from the server
        rw_timeout = _params.get('rw_timeout', 1)  # Timeout [sec] on blocking read/write
        response_timeout = _params.get('response_timeout', 1)  # Timeout [sec] for radio to response to a command
        many = _params.get('many', 9999999)  # Max size of read buffer
        prompt_retries = _params.get('prompt_retries', 5)  # The number of times to attempt and get the CLI prompt
        terminal_height = _params.get('terminal_height', 5000)  # Number of rows in VT100 terminal
        log_enable = _params.get('log_enable', True)  # Enable logging
        log_dir = _params.get('log_dir', 'ssh_logs')  # Directory for log files
        log_level_console = _params.get('log_level_console',
                                        'CRITICAL')  # Console logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_level_file = _params.get('log_level_file',
                                     'INFO')  # File logger level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        del _params

    # Check log_dir exists, or else create it
    if log_enable:
        # Create log_dir if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        else:
            if not os.path.isdir(log_dir):
                raise OSError(f"Directory '{log_dir}' exists as a file")

    def __init__(self, ip_addr: str | ipaddress.IPv4Address, username: str = 'admin', password: str = 'admin'):
        """ Create a new instance of class :class:`SikCli`, initiates attributes and calls :meth:`connect`

            :param ip_addr: IP address for radio
            :type ip_addr: str
            :param username: Username for logging into the radio (default: `admin`)
            :type username: str
            :param password: Password for logging into the radio (default: `admin`)
            :type password: str
        """

        #: IP address for CLI session
        self.ip_addr = ip_addr
        #: Username for CLI session
        self.username = username
        #: Password for CLI session
        self.password = password
        self._logger = self._logger_init()
        self._channel = None  # Paramiko Channel object
        self._transport = None  # Paramiko Transport object
        #: SSH banner (if available from radio)
        self.banner = ''
        #: Radio model (if derivable from :attr:`banner` and/or :attr:`prompt`)
        self.model = ''
        #: Name of radio. Could be the radio dialled into (whose IP address is :attr:`ip_addr`), or a TG radio tunneled into
        self.name = ''
        #: CLI prompt (applicable only to TG radios)
        self.prompt = ''
        #: Radio serial number (if derivable from :attr:`banner` and/or :attr:`prompt`)
        self.sn = ''
        #: Radio software version (if derivable from :attr:`banner` and/or :attr:`prompt`)
        self.sw = ''
        #: List of intermediate radios tunneled through to reach the current radio (identified by :attr:`name`)
        #: Empty list designates no tunneling. Applicable to TG radios only
        self.tunnel_stack = []
        #: Last error logged (if any)
        self.last_err = ''
        #: Instance of a `Paramiko Client <https://docs.paramiko.org/en/stable/api/client.html>`_
        self.ssh = paramiko.SSHClient()  # ssh is an instance of a Paramiko Client
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Tolerate unknown SSH host_keys
        # Attempt to open an SSH connection and retrieve the SSH banner
        self.connect()
        # Attempt to retrieve the CLI prompt
        # self._get_prompt()

    def __del__(self):
        self.disconnect()

    def __repr__(self):
        info = f"SIKLU_SSH('{self.ip_addr}', "
        info += f"username='{self.username}', password='{self.password}')"
        return info

    def __str__(self):
        info = f"{__class__.__name__}"
        info += f"\tip_addr: {self.ip_addr}\n"
        info += f"\tusername: {self.username}\n"
        info += f"\tpassword: {self.password}\n"
        info += f"\tconnected: {self.is_connected()}\n"
        info += f"\tbanner: {self.banner}\n"
        info += f"\tmodel: {self.model}\n"
        info += f"\tsn: {self.sn}\n"
        info += f"\tsw: {self.sw}\n"
        info += f"\tprompt: {self.prompt}\n"
        info += f"\tname: {self.name}"
        if len(self.tunnel_stack) > 0:
            info += f" (tunneled into via: {', '.join(self.tunnel_stack)})"
        info += f"\n\tlast_err: {self.last_err}"
        return info

    def _derive_model(self):
        """ Extract model, name, sn and sw from banner or prompt
        """
        self.sn = ''
        self.sw = ''
        self.model = ''
        self.name = ''
        if self.banner:
            # Extract the model name
            index = self.banner.find(',')
            self.model = self.banner[0:index].strip() if index > 0 else ''
            # Extract the serial number (S/N)
            r = re.search(r'S/N:\s*(.*)(?=,)', self.banner, re.I)
            self.sn = '' if r is None else r[1].strip()
            # Extract the SW version
            r = re.search(r'Ver:\s*(.+)', self.banner)
            self.sw = '' if r is None else r[1].strip()
            if self.model:
                string = f"model: {self.model}, sn: {self.sn}, sw: {self.sw}"
                self._logger.info(f"{self._logger_prefix()}: Identifies via banner as {string}")
            else:
                error_msg = f"May not be a Siklu radio - banner: '{self.banner}'"
                self.last_err = error_msg
                self._logger.info(f"{self._logger_prefix()}: {error_msg}")
        if self.prompt:
            # MH TG
            if m := re.match(r'(MH-\S+)@(\S+)>', self.prompt):
                self.model = m[1]
                self.name = m[2]
                self._logger.info(f"{self._logger_prefix()}: Identifies via prompt as {self.model}@{self.name}")
            # EH and classic MH
            elif m := re.match(r'(.+)>', self.prompt):
                if self.model:  # Banner encountered, and model extracted
                    self.name = m[1]
                    self._logger.info(f"{self._logger_prefix()}: Identifies via prompt as {self.name}")
                else:  # Added for EH-8010FX running 10.6.2 where the banner went missing
                    response = self.send('show inventory 1')
                    if m1 := re.match(r'inventory 1 desc\s+:\s+(\S+)', response):
                        self.name = m[1]
                        self.model = m1[1]
                        self._logger.info(
                            f"{self._logger_prefix()}: Identifies via prompt/inventory as {self.model}@{self.name}")
                        if m1 := re.search(r'inventory 1 serial\s+:\s+(\S+)', response):
                            self.sn = m1[1]
                        if m1 := re.search(r'inventory 1 sw-rev\s+:\s+(\S+)', response):
                            self.sw = m1[1]
                    else:
                        error_msg = f"May not be a Siklu radio - prompt: '{self.prompt}'"
                        self.last_err = error_msg
                        self._logger.info(f"{self._logger_prefix()}: {error_msg}")
            else:
                error_msg = f"May not be a Siklu radio - prompt: '{self.prompt}'"
                self.last_err = error_msg
                self._logger.info(f"{self._logger_prefix()}: {error_msg}")
        return None

    def _get_transport_and_banner(self):
        """ Get the Transport object from Paramiko, and derive the SSH banner (if available)
        """
        self.banner = ''
        self._transport = self.ssh.get_transport()
        if self._transport:
            banner = self._transport.get_banner()
            if banner:
                self.banner = banner.decode().strip()
        return None

    def _get_prompt(self):
        """ Get the CLI prompt by sending an empty command (CRLF)
        """
        self.prompt = ''
        if self.is_connected():
            retries = 0
            prompt = ''
            while prompt == '' and retries < self.prompt_retries:
                prompt = self.send('', remove_prompt=False)
                retries += 1
            if m := re.match(r'(\S+>)', prompt):
                self.prompt = m[1]
        return None

    def _logger_init(self) -> logging.Logger:
        """ Set up logger with two handlers: console and file
        """
        # Create logger and set level to the minimum of the console handler and file handler
        logger = logging.getLogger(str(self.ip_addr))
        if self.log_enable:
            logger.setLevel(logging.DEBUG)
            # Create logger file handler
            filename = os.path.join(self.log_dir, f"sikssh.{str(self.ip_addr)}.log")
            fh = logging.FileHandler(filename)
            # Create logger console handler
            ch = logging.StreamHandler()
            # Set levels for each handler
            fh.setLevel(self.log_level_file)
            ch.setLevel(self.log_level_console)
            # Set Formatter:
            formatter = logging.Formatter("%(asctime)s - %(levelname)7s - %(message)s")
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            # Add handlers to logger
            logger.addHandler(fh)
            logger.addHandler(ch)
        else:
            logger.disabled = True
        return logger

    def _logger_prefix(self) -> str:
        """ This is a prefix to prepend all logged events"""
        if self.tunnel_stack:
            return f"{self.username}@{self.ip_addr}:{self.name}"
        else:
            return f"{self.username}@{self.ip_addr}"

    def connect(self) -> bool:
        """ Create an SSH connection and a virtual terminal to radio. Attempt to obtain the banner and/or prompt
            and from these derive the following attributes:

            =============== =============================
            Attribute       Derived from
            =============== =============================
            :attr:`model`   :attr:`banner`, :attr:`prompt`
            :attr:`name`    :attr:`prompt`
            :attr:`sn`      :attr:`banner`
            :attr:`sw`      :attr:`banner`
            =============== =============================

            This method is called automatically when instantiating the :class:`SikCli`.
            It may be called manually after calling :meth:`disconnect`.

            Return True if successful, otherwise False.
            """
        if self.is_connected():  # already connected:
            return True
        else:  # attempt to connect as SSH Client
            self._logger.debug(f"{self._logger_prefix()}: Attempting to connect via SSH")
            self.last_err = ''
            try:
                self.ssh.connect(self.ip_addr,
                                 username=self.username,
                                 password=self.password,
                                 timeout=self.tcp_timeout,
                                 banner_timeout=self.banner_timeout,
                                 auth_timeout=self.auth_timeout)
            except paramiko.AuthenticationException:
                self.last_err = 'Authentication failed'
            except paramiko.SSHException:
                self.last_err = 'Unspecified SSH Error in connecting to device'
            except socket.timeout:
                self.last_err = ' Socket timeout'
            except paramiko.ssh_exception.NoValidConnectionsError:
                self.last_err = 'Connection refused to port 22'
            except:
                self.last_err = 'Unknown ssh error at non-specific except'
            else:  # SSH Client connected. Attempt to open channel as terminal
                try:
                    self._channel = self.ssh.invoke_shell(height=self.terminal_height)
                except (paramiko.SSHException, AttributeError):
                    self.last_err = "Unspecified SSH failure in attempting to invoke a shell"
                else:
                    self._channel.settimeout(self.rw_timeout)  # timeout on blocking RW
            if self.last_err:
                self._logger.error(f"{self._logger_prefix()}: {self.last_err}")
                self.disconnect()
                return False
            # Proceed on the basis that SSH Terminal is open and no errors
            self._get_transport_and_banner()
            self._get_prompt()
            self._derive_model()
            self._logger.info(f"{self._logger_prefix()}: Connected and shell terminal established")
            return True

    def disconnect(self):
        """ Disconnect SSH session and close CLI virtual terminal. Reset values for:
            :attr:`banner`, :attr:`last_err`, :attr:`model`, :attr:`name`, :attr:`prompt`, :attr:`sn`,
            :attr:`sw`, :attr:`tunnel_stack`.
            """
        self.ssh.close()
        self._channel = None
        self.banner = ''
        self.prompt = ''
        self._derive_model()
        self.tunnel_stack = []
        self.prompt = ''
        if self._transport:  # report disconnection if session was meant to be open
            self._logger.debug(f"{self._logger_prefix()}: Disconnected")
            self._transport = None
        return None

    def is_connected(self) -> bool:
        """ Returns True if the SSH session the CLI virtual terminal are open, otherwise False.
        """
        if not self._transport:  # Expecting connection to be closed
            return False
        elif (self._channel.closed or  # Expecting connection to be open but isn't
              not self._channel.active or
              not self._channel or
              not self._transport.is_active() or
              not self._transport.is_authenticated()):
            err_msg = 'Connection found to be unexpectedly disconnected'
            self._logger.error(f"{self._logger_prefix()}: {err_msg}")
            self.last_err = err_msg
            self.disconnect()  # close the connection
            return False
        else:
            return True

    def send(self, cmd: str, remove_prompt: bool = True) -> str:
        """ Send a command to an open CLI virtual terminal (append CRLF if necessary), and return
            the response (either with or without the trailing prompt).

            :param cmd: Command to send to CLI terminal
            :type cmd: str
            :param remove_prompt: Strips the trailing prompt from the response if True, keep trailing prompt if False
            :type remove_prompt: bool
            :return: Response to command (or empty string if problem encountered)
            :rtype: str
            """
        # Append a CR to cmd (if necessary)
        cmd = cmd.strip()
        cmd_to_send = cmd + '\n'
        if self.is_connected():  # Attempt to send cmd
            try:
                # Clear receive buffer (if necessary)
                if self._channel.recv_ready():
                    _ = self._channel.recv(self.many)
                # Send command and sleep
                self._channel.send(cmd_to_send)
                time.sleep(self.response_timeout)
                # Receive response
                # if self.channel.recv_ready():
                response = self._channel.recv(self.many)
            except socket.error:
                err_msg = f"Command '{cmd}' may not have been sent due to socket error"
                self._logger.warning(f"{self._logger_prefix()}: {err_msg}")
                return ''
            else:
                # Remove cmd echo from response
                if response:
                    response_no_cmd = response.decode().replace(cmd, '').strip()
                    if response_no_cmd:
                        if cmd:
                            self._logger.info(f"{self._logger_prefix()}: Sent command: '{cmd}'")
                        if remove_prompt and self.prompt:
                            while self.prompt in response_no_cmd:
                                response_no_cmd = response_no_cmd.replace(self.prompt, '')
                        if '@' in response_no_cmd and cmd == 'show':
                            print()
                        return response_no_cmd.strip() + ' '
                self._logger.warning(f"{self._logger_prefix()}: No response to command '{cmd}'")
                return ''
        else:
            self._logger.warning(f"{self._logger_prefix()}: Command '{cmd}' not sent: ssh disconnected")
            return ''

    def tunnel_in(self, remote_name) -> bool:
        """
        Tunnel into a remote radio using the 'connect' CLI command (applicable for TG radios only).
        Updates :attr:`name`, :attr:`tunnel_stack`.

        :param remote_name: name of remote radio
        :type remote_name: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if self.is_connected():
            _ = self.send(f"connect {remote_name}")
            self.tunnel_stack.append(self.name)
            self._get_prompt()
            self._derive_model()
            if self.name == remote_name:
                self._logger.info(f"{self._logger_prefix()}: Successfully tunneled into {remote_name}")
                return True
            else:
                self.tunnel_stack.pop()
                err_msg = f"Unable to tunnel into '{remote_name}'"
                self._logger.error(f"{self._logger_prefix()}: {err_msg}")
                self.last_err = err_msg
                return False
        else:
            return False

    def tunnel_out(self) -> bool:
        """
        Tunnel out of a remote radio using the 'quit' CLI command (applicable for TG radios only).
        Updates :attr:`name`, :attr:`tunnel_stack`.

        :return: True if successful, False otherwise
        :rtype: bool
        """
        if self.is_connected():
            if self.tunnel_stack:
                _ = self.send(f"quit")
                self.tunnel_stack.pop()
                self._get_prompt()
                self._derive_model()
                self._logger.info(f"{self._logger_prefix()}: Successfully terminated tunnel")
                return True
            else:
                error_msg = "Unable to tunnel out - already at top hierarchy"
                self.last_err = error_msg
                self._logger.warning(f"{self._logger_prefix()}: {error_msg}")
                return False
        else:
            return False
