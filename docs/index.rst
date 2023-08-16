.. Batchscanner documentation master file, created by
   sphinx-quickstart on Tue Aug 15 16:22:14 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Quickstart for Batchscanner
===========================================

:Version: |version|

Batchscanner is a program to batch-query or batch-configure multiple Siklu radios
via their CLI (SSH) interface.
It operates over a user-defined range of IP addresses and/or networks, and supports
the following *actions*:

- **scan**: For each IP address, identify if the device is a Siklu radio, and if so what kind.
  Information is extracted from the SSH banner (if one exists) or else from the CLI prompt.
- **show**: executes CLI 'show' commands to extract key metrics from each radios (e.g., link status: up/down).
- **script**: executes a sequence of commands read from text file.
- **set_tod**: configure the date and time of the radios based on that of the computer (running Batchscanner).

Actions can be applied to specific types of radios, according to the following classification:

- **EH**: Etherhaul radios
- **BU**: Classic MultiHaul base units (BUs)
- **TU**: Classic MultiHul terminal units (TUs)
- **TG**: MultiHaul TG radios. For these radios, there is a further option for Batchscanner to action over remote CNs
  (which may not have unique IP addresses).
		
Results are written to text and/or csv files.


.. note::
   This program is a personal contribution. It is not affiliated with `Siklu Communications <https://www.siklu.com>`_
   in any way, and does not contain any Siklu proprietary and/or confidential information.
   
Usage
======

Running as a python script:

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
	  -n NETWORK_FILENAME   Filename specifying the Network (range of IP addresses to scan and login credentials.
				Default: 'network.txt'
	  -c CONFIG_FILENAME    Configuration file for overriding default program parameters.
				Default: 'config.toml'



Technical Documentation
=========================

Complete

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
