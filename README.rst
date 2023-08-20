
**Project still under development.**

``Batchscanner`` is a program to batch-query or batch-configure multiple Siklu radios
via their CLI (SSH) interface.
It operates over a user-defined range of IP addresses and/or networks, executes some action,
and writes the results to csv/txt files.

.. note:: This program is a personal initiative and contribution.
   Although it is designed
   for managing radios by `Siklu Communications <https://www.siklu.com>`_, no use
   has been made of any company resources, nor any intellectual proprietary nor
   confidential information.

`Batchscanner` is a program to batch-query or batch-configure
multiple Siklu radios via their CLI (SSH) interface.
It operates over a user-defined range of IP addresses and/or networks, and supports
the following *actions*:

 - **scan**: For each IP address, identify if the device is a Siklu radio, and if so what kind.
   Information is extracted from the SSH banner (if one exists) and/or from the CLI prompt.
 -  **show**: executes CLI 'show' commands to extract key metrics from each radios (e.g., link up/down).
 - **script**: executes a sequence of commands read from text file.
 - **set_tod**: configure the date and time of the radios based on that of the computer (running Batchscanner).

Actions can be applied to specific types of radios,
according to the following classification:

 - **EH**: Etherhaul radios
 - **BU**: Classic MultiHaul base units (BUs)
 - **TU**: Classic MultiHul terminal units (TUs)
 - **TG**: MultiHaul TG radios. For these radios, there is a further option for `Batchscanner` to action
   over remote CNs (which may not have unique IP addresses).

Results are written to text and/or csv files.


Usage
======

Running as a python script:

.. _usage:

.. code-block:: none

	Usage: python -m batchscanner [-h] [-a {scan,show,script,set_tod}] [-n NETWORK_FILENAME] [-c CONFIG_FILENAME]

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

Example content of network file defining a total of 1 + 200 + 252 IP addresses

.. code-block::

   username = admin
   password = admin
   192.168.0.1
   10.11.12.1 - 10.11.12.200
   10.10.10.0/24


Config file
--------------

The configuration file (simple `TOML <https://toml.io/en/>`_  format) may be used to override
the default program parameters. For a list of these parameters and their respective
meanings, refer to `project documentation <https://batchscanner.readthedocs.io/en/latest/>`_.

Example content of config file

.. code-block::

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


