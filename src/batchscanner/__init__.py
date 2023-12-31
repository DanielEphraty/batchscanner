"""  A CLI batch tool for Siklu radios.

Script usage: batchscanner [-h] [-a {scan,show,script,set_tod}] [-n NETWORK_FILENAME] [-c CONFIG_FILENAME]

options:
  -h, --help            show this help message and exit
  -a {scan,show,script,set_tod}
                        Action for batchscanner to take (default: show). One of:
                            scan: scan the network and identify which IP address is a Siklu radio;
                            show: extract key metrics from radios (parsed outputs of 'show' commands);
                            script: execute a script: send list of commands read from text file;
                            set_tod: set date and time.
  -n NETWORK_FILENAME   Mandatory filename specifying the Network (range of IP addresses to scan and login credentials).
                        Default: 'network.txt'
  -c CONFIG_FILENAME    Optional configuration file for overriding default program parameters.
                        Default: 'config.toml'

"""

__author__ = 'Daniel Ephraty'
__version__ = '0.1.7'



