Quickstart
===========================================

:program:`Batchscanner` is a script to batch-scan and/or query and/or configure
multiple `Siklu Communications <https://www.siklu.com>`_ radios
via their CLI (SSH) interface.
It operates over a user-defined range of IP addresses and/or networks, and supports
the following *actions*:

 - **scan**: For each IP address, identify if the device is a Siklu radio, and if so what kind.
   Information is extracted from the SSH banner (if one exists) and/or from the CLI prompt.
 -  **show**: executes CLI 'show' commands to extract key metrics from each radios (e.g., link up/down).
 - **script**: executes a sequence of commands read from text file.
 - **set_tod**: configure the date and time of the radios based on that of the computer.

Actions can be applied to specific types of radios,
according to the following classification:

 - **EH**: Etherhaul radios
 - **BU**: Classic MultiHaul base units (BUs)
 - **TU**: Classic MultiHul terminal units (TUs)
 - **TG**: MultiHaul TG radios. For these radios, there is a further option for batchscanner to action
   over remote *Client Nodes* (CNs) (which may not have unique IP addresses).

Results are written to text and/or csv files.

:program:`Batchscanner` is currently released as a command-line script / executable.
The program collects some parameters via command-line argument and text files,
and then calls the main batchscanner API.

Installation
=============

As a standalone (executable) script
------------------------------------

This option does not require a Python environment set up.

#. Download one of the following zip files based on your OS:

   - Windows 64bit:
     `download link <https://github.com/DanielEphraty/batchscanner/releases/latest/download/batchscanner-x64.zip>`_

#. Extract the zip file to your local drive

As a Python script
--------------------

.. code-block:: shell

   $ pip install batchscanner-siklu

Usage
======

#. Use a standard text editor to edit the default `network file <Network file_>`_ `network.txt` to specify
   the range of IP addresses, and log-in credentials to the radio.
   Alternatively, create a new file and refer to it with the -c option (below).
#. If required, use a standard text editor to edit the default program
   `configuration file <Config file_>`_ `config.toml`.
   Alternatively, create a new file and refer to it with the -p option (below).
#. Run the program:

   .. code-block:: none

      Usage: batchscanner [-h] [-a {scan,show,script,set_tod}] [-n NETWORK_FILENAME] [-c CONFIG_FILENAME]

      options:
          -h, --help            Show this help message and exit
          -a {scan,show,script,set_tod}
                    Action for batchscanner to take (default: show). One of:
                        scan: scan the network and identify which IP address is a Siklu radio;
                        show: extract key metrics from radios (parsed outputs of 'show' commands);
                        script: execute a script: send list of commands read from text file;
                        set_tod: set date and time.
          -n NETWORK_FILENAME   Mandatory filename specifying the Network (range of IP addresses to scan and login credentials.
                    Default: 'network.txt'
          -c CONFIG_FILENAME    Optional configuration file for overriding default program parameters.
                    Default: 'config.toml'

Network file
--------------

The range of IP addresses is specified as a text file, with the following format:

 * Username and password to log into the radios
 * A range of IP addresses, described by any number of the following (which can be mixed and matched):

    - A single IP address
    - A range of IP addresses: start and end addresses, separated by a hyphen
    - A subnet with a forward slash denoting the number of subnet bits.

.. code-block:: shell
   :caption: Example content of network file defining a total of 1 + 200 + 252 IP addresses:

   username = admin
   password = admin
   192.168.0.1
   10.11.12.1 - 10.11.12.200
   10.10.10.0/24

Further details available :func:`here <batchscanner.credentials.Credentials.__init__>`.

Config file
--------------

The configuration file (simple `TOML <https://toml.io/en/>`_  format) may be used to override
the default program parameters. For a list of these parameters and their respective
meanings, refer to the *Parameters* section :func:`~batchscanner.batchscan.run_batch`.

.. code-block:: shell
   :caption: Example content of configuration file:

    batch_size = 1000                     # Number of IP addresses in single batch (results saved after each batch)
    script_filename = 'script.txt'        # filename containing list of commands to send to radio (applicable only if action='script')
    include_eh = true                     # If true, action EtherHaul radios
    include_bu = true                     # If true, action MultiHaul BU radios
    include_tu = true                     # If true, action MultiHaul TU radios
    include_tg = true                     # If true, action MultiHaul TG radios
    include_tg_remote_cns = false         # If true, action all remote CNs (applicable only to TG DNs)
    multiprocessing_flag = true           # If true, Run concurrently (much faster running time)
    multiprocessing_num_processes = 50    # Number of processes to run concurrently
    output_directory = 'output'           # Results are written to this directory
    save_show_tg_per_radio = false        # If true, save also parsed 'show' output per radio (applicable only to TG)
    save_show_tg_per_radio_raw = false    # If true, save aso the raw (unparsed) 'show' output per radio (applicable only to TG)
    time_shift = 0                        # Number of hours to add to computer time when configuring date/time (applicable only if action='set_tod')



