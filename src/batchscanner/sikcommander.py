import datetime
from dataclasses import dataclass
import re
from typing import Iterable

from batchscanner.sikssh import SikSsh
from batchscanner.sikcredentials import SikCredential
from batchscanner.parsers.parse_show_eh import SikShowEh
from batchscanner.parsers.parse_show_tg import SikShowTg


@dataclass
class SikCommand:
    """ Dataclass for conveniently grouping a CLI command to a radio, the CLI response, and other related parameters.
    """

    #: Command text (e.g.: 'show system') - user configured.
    command: str
    #: Identifying label for the target radio (typically IP address and/or radio name) - user configured.
    target_id: str = ""
    #: The CLI response to :attr:`command` - updated after the command is executed.
    response: str = ""
    #: Boolean flag indicating  if command executed successfully - updated after :attr:`command` is executed.
    success: bool = False

    def __repr__(self):
        max_len = 50
        string = f"SikCommand(command={self.command}, "
        string += f"target_id={self.target_id}, "
        string += f"success={self.success}, "
        if len(self.response) > max_len:
            string += f"response={self.response[:max_len]!r}...)"
        else:
            string += f"response={self.response!r})"
        return string

    def copy(self):
        """ A method for creating a (deep) copy of :class:`SikCommand`.
        """

        return SikCommand(command=self.command,
                          target_id=self.target_id,
                          response=self.response,
                          success=self.success)

    def as_dict(self, *, max_response_len: int = 50) -> dict:
        """ A method for representing a class instance as dictionary.

            :param max_response_len: Maximum number of characters to include for the response.
                                     Responses that are truncated are postpended by an ellipsis.
            :type max_response_len: int
            :return: A dictionary representing the class instance.
            :rtype: dict
        """
        output = {'target_id': self.target_id,
                  'command': self.command,
                  'success': self.success}
        if len(self.response) > max_response_len:
            output['response'] = self.response[:max_response_len] + '...'
        else:
            output['response'] = self.response
        return output


class SikCommander:
    """ A wrapper for :class:`sikcli_ssh.SikCLI` providing higher-level methods
        for sending script to Siklu radios, as well as scanning them.
    """

    def __init__(self, credential: SikCredential, include_tg_remote_cns: bool = False):
        """ Create a new class instance and initiate attributes

        :param credential: A Dataclass for storing radio’s login credentials: IP address, username, and password
                           (refer to :class:`SikCredential`).
        :type credential: SikCredential
        :param include_tg_remote_cns: Relevant for TG radios only. If True, automatically repeat methods
                                      :meth:`show_tg` and :meth:`set_tod_tg` to all remote CN radios.
        :type include_tg_remote_cns: bool
        """

        #: Radio’s login credentials: IP address, username, and password (instance of :class:`SikCredential`).
        self.credential = credential
        #: Relevant for TG radios only. If True, automatically repeat methods to all remote CN radios.
        self.include_tg_remote_cns = include_tg_remote_cns
        #: List of accumulated errors when transacting with radio.
        self.errors = []
        cli = SikSsh(str(credential.ip_addr), credential.username, credential.password)
        #: Instance of :class:`sikcli_ssh.SikSsh` (CLI session with radio).
        self.cli = cli
        #: Boolean flag indicating if the CLI session :attr:`cli` is connected.
        self.connected = cli.is_connected()
        if cli.last_err:
            self.errors.append(cli.last_err)
        #: Radio model.
        self.model = cli.model
        #: Radio type: EH, BU (classic MH), TU (classic MH), TG.
        self.radio_type = self._derive_radio_type()
        #: Radio name.
        self.name = cli.name
        #: Radio serial number.
        self.sn = cli.sn
        #: Radio software version.
        self.sw = cli.sw
        #: List of script sent to radio (each element in the list is :class:`SikCommand`).
        self.commands_sent = []
        #: List of remote radios (relevant for TG only). Populated only if :attr:`include_tg_remote_cns` is True,
        #: and an attempt to extract remote CN radios is successful. Otherwise, an empty list.
        self.tg_remote_cns = []
        if self.radio_type == 'TG' and include_tg_remote_cns:
            self.get_tg_remote_cns()
        #: Output of action taken by Commander
        self.output = []

    def __repr__(self):
        return f"SikCommander(credential={self.credential}, include_tg_remote_cns={self.include_tg_remote_cns})"

    def __str__(self):
        string = f"SikCommander:\n"
        string += f"\tcredential: {self.credential}\n"
        string += f"\tinclude_tg_remote_cns: {self.include_tg_remote_cns}\n"
        string += f"\tconnected: {self.connected}\n"
        string += f"\terrors: {self.errors}\n"
        string += f"\tmodel: {self.model}\n"
        string += f"\tname: {self.name}\n"
        string += f"\tradio_type: {self.radio_type}\n"
        string += f"\tsw: {self.sw}\n"
        string += f"\tsn: {self.sn}\n"
        string += f"\ttg_remote_cns: {self.tg_remote_cns}\n"
        string += f"\tcommands_sent: {self.commands_sent}\n"
        string += f"\toutput: {self.output}\n"
        return string

    def _derive_radio_type(self) -> str:
        """ Determine the (family) type of radio, based on :attr:`model`.

            :return: 'EH' if radio is an EtherHaul radio,
                     'BU' if radio model is MH-B100,
                     'TU' if radio model is MH-T200 or MH-T201,
                     'TG' if radio is a TG radio. If known, return an empty string.
            :rtype: str

            :meta public:
        """

        if self.model:
            if re.match(r'EH', self.model):
                return 'EH'
            elif re.match(r'MH-B100', self.model):
                return 'BU'
            elif re.match(r'MH-T200|MH-T201', self.model):
                return 'TU'
            elif re.match(r'MH-', self.model):
                return 'TG'
            else:
                return ''
        else:
            return ''

    def as_dict(self) -> dict:
        """ Represent an instance of :class:`SikCommander` as a dictionary.

            :return: Dictionary including keys: :attr:`ip_addr`, :attr:`radio_type`, :attr:`model`,
                                                :attr:`name`, :attr:`sw`, :attr:`sn`, and
                                                the last error listed in :attr:`errors`.
            :rtype: dict
        """
        output = {'ip_addr': str(self.credential.ip_addr),
                  'radio_type': self.radio_type,
                  'model': self.model,
                  'name': self.name,
                  'sw': self.sw,
                  'sn': self.sn,
                  }
        # Look for the last error, excluding errors as a direct result of a command sent
        if self.errors:
            for error in self.errors[::-1]:
                if len(error) > 8 and error[:8] == 'Command:':
                    continue
                else:
                    output['last_non_cmd_error'] = error
                    break
        else:
            output['last_non_cmd_error'] = ''
        return output

    def send_cmds(self, commands: Iterable[str], target_id="") -> list[SikCommand]:
        """ Send each command in `script` to radio. Each command is returned as :class:`SikCommand`, where:

             * :attr:`SikCommand.command` is a copy of the command,
             * :attr:`SikCommand.target_id` is an optional method argument, or else assigned as below,
             * :attr:`SikCommand.response` is the response from the radio
             * :attr:`SikCommand.success' indicates if the command executed successfully.

            After execution, each :class:`SikCommand` is appended to :attr:`commands_sent`.
            Errors (if any) are appended to :attr:`errors`.

            :param commands: An iterable of script.
            :type commands: Iterable[str]
            :param target_id: An optional string which is inserted into each :attr:`SikCommand.target_id`.
                              If omitted, automatically assigned as 'radio IP: radio name'.
            :type target_id: str
            :return: A list of :class:`SikCommand`, as explained above.
            :rtype: list[SikCommand]
        """
        sik_commands = [SikCommand(command) for command in commands]
        if not target_id:
            target_id = f"{str(self.credential.ip_addr)}: {self.name}"
        for command in sik_commands:
            command.target_id = target_id
            command.response = self.cli.send(command.command)
            if command.response:
                command.success = True
                if any(err in command.response for err in ('Ambiguous command',
                                                           'CLI syntax error',
                                                           'Validate failed',
                                                           'Error:',
                                                           'Invalid',)):
                    command.success = False
                    self.errors.append(
                        f"Command: '{command.command}' to '{target_id}' raised an error: '{command.response}'")
            else:
                command.success = False
                self.errors.append(f"Command: '{command.command}' to '{target_id}' failed")
        self.commands_sent.extend(sik_commands)
        return sik_commands

    def send_cmds_remote_cns(self, commands: Iterable[str]) -> list[SikCommand]:
        """ Send script (in `script`) to all remote TG CNs listed in :attr:`tg_remote_cns`:
             1. Tunnel into a CN
             2. Send script by calling :meth:`send_cmds` with `target_id` assigned as:
                'radio IP: radio name' -> 'remote CN name'
             3. Tunnel out

            After execution, each :class:`SikCommand` is appended to :attr:`commands_sent`.
            Errors (if any) are appended to :attr:`errors`.

            :param commands: A list of script.
            :type commands: list[SikCommand]
            :return: EXPLAIN BETTER A list comprising replicates of `script`, where each replicate is
                     a deep-copy of `script`, after sending to one of the CN radios.
                     :class:`SikCommand` attributes updated per :meth:`send_cmds`, where
                     `target_id` is automatically assigned as: 'radio IP: radio name' -> 'remote CN name'.

            :rtype: list[SikCommand]
        """
        commands_out = []
        for cn in self.tg_remote_cns:
            if self.cli.tunnel_in(cn):
                target_id = f"{str(self.credential.ip_addr)}: {self.name} -> {cn}"
                commands_out.extend(self.send_cmds(commands, target_id))
                self.cli.tunnel_out()
        return commands_out

    def get_tg_remote_cns(self):
        commands_in = ['show radio-common',
                       'show radio-dn',
                       ]
        commands_out = self.send_cmds(commands_in)
        response = commands_out[0].response + '\n' + commands_out[1].response
        identifier = f"{self.credential.ip_addr}: {self.name}"
        show = SikShowTg(response, identifier)
        self.tg_remote_cns = [str(link.remote) for link in show.links if
                              link.status == 'active' and link.link_type == 'cn']
        return commands_out

    def show_eh(self):
        """
        #
        :return:
        """
        show_cmds = (SikShowEh.showsystem(),
                     SikShowEh.showsw(),
                     SikShowEh.showinventory(),
                     SikShowEh.showrf(),
                     SikShowEh.showrfdebug(),
                     SikShowEh.showeth1(),
                     SikShowEh.showeth2(),
                     SikShowEh.showeth3(),
                     SikShowEh.showeth4(),
                     SikShowEh.showlldp(),
                     SikShowEh.showlog(2),
                     )
        output = {'ip_addr': self.credential.ip_addr}
        commands = self.send_cmds([cmd for cmd, _ in show_cmds])
        params = (param for _, param in show_cmds)
        for command, param in zip(commands, params):
            output.update(SikShowEh.parse(command.response, param))
        self.output.append(output)

    def show_bu(self):
        show_cmds = (SikShowEh.showsystem(),
                     SikShowEh.showsw(),
                     SikShowEh.showinventory(),
                     SikShowEh.showeth1(),
                     SikShowEh.showeth2(),
                     SikShowEh.showeth3(),
                     SikShowEh.showlldp(),
                     SikShowEh.showlog(2),
                     SikShowEh.showbaseunit(),
                     SikShowEh.showremoteterminalunit(),
                     )
        output = {'ip_addr': self.credential.ip_addr}
        commands = self.send_cmds([cmd for cmd, _ in show_cmds])
        params = (param for _, param in show_cmds)
        for command, param in zip(commands, params):
            output.update(SikShowEh.parse(command.response, param))
        self.output.append(output)

    def show_tu(self):
        show_cmds = (SikShowEh.showsystem(),
                     SikShowEh.showsw(),
                     SikShowEh.showinventory(),
                     SikShowEh.showeth1(),
                     SikShowEh.showeth2(),
                     SikShowEh.showeth3(),
                     SikShowEh.showlldp(),
                     SikShowEh.showlog(2),
                     SikShowEh.showterminalunit(),
                     )
        output = {'ip_addr': self.credential.ip_addr}
        commands = self.send_cmds([cmd for cmd, _ in show_cmds])
        params = (param for _, param in show_cmds)
        for command, param in zip(commands, params):
            output.update(SikShowEh.parse(command.response, param))
        self.output.append(output)

    def show_tg(self):
        """ Parse the output of 'show' command sent to a TG radio, and append the result
            (represented as :class:`SikShowTg`) to :attr:`commands_sent`.
            Automatically repeated for all radios listed in :attr:`tg_remote_cns`.

            :return: None
        """

        commands_in = ['show']
        commands_out = self.send_cmds(commands_in)
        commands_out.extend(self.send_cmds_remote_cns(commands_in))
        for command in commands_out:
            if command.success:
                show = SikShowTg(command.response, command.target_id)
                self.output.append(show)
        return None

    def set_tod(self, hours_shift: float = 0):
        """ Configure the date and time for EH/MH radios. The date and time are copied from those of the PC
            (running this program) with the addition of `hours_shift` (to compensate for different time zones).

            :param hours_shift: delta hours added to the PC's time before sending to radio. For example,
                                if PC time is 08:00 and `hours_shift` equals 2.5, the time configured to radio
                                will be 10:30. The default for `hours_shift` is zero.
            :type hours_shift: float
        """
        tod = datetime.datetime.now() + datetime.timedelta(hours=hours_shift)
        commands_in = [f"set system time {tod.strftime('%H:%M:%S')}",
                       f"set system date {tod.strftime('%Y.%m.%d')}",
                       ]
        _ = self.send_cmds(commands_in)

    def set_tod_tg(self, hours_shift: float = 0):
        """ Configure the date and time for a TG radio. The date and time are copied from those of the PC
            (running this program) with the addition of `hours_shift` (to compensate for different time zones).
            Automatically repeated for all radios listed in :attr:`tg_remote_cns`.

            :param hours_shift: delta hours added to the PC's time before sending to radio. For example,
                                if PC time is 08:00 and `hours_shift` equals 2.5, the time configured to radio
                                will be 10:30. The default for `hours_shift` is zero.
            :type hours_shift: float
        """
        tod = datetime.datetime.now() + datetime.timedelta(hours=hours_shift)
        commands_in = [f"set time {tod.strftime('%H:%M:%S')}",
                       f"set date {tod.strftime('%Y-%m-%d')}",
                       ]
        _ = self.send_cmds(commands_in)
        # Send script to remote CNs. Not using send_cmds_remote_cns because delay will render time inaccurate
        if self.include_tg_remote_cns:
            for cn in self.tg_remote_cns:
                if self.cli.tunnel_in(cn):
                    target_id = f"{str(self.credential.ip_addr)}: {self.name} -> {cn}"
                    # Get updated TOD
                    tod = datetime.datetime.now() + datetime.timedelta(hours=hours_shift)
                    commands_in = [f"set time {tod.strftime('%H:%M:%S')}",
                                   f"set date {tod.strftime('%Y-%m-%d')}",
                                   ]
                    _ = self.send_cmds(commands_in, target_id)
                    self.cli.tunnel_out()

