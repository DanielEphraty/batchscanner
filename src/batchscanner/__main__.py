""" A command-line script for launching batchscanner """

import argparse
import multiprocessing
from sys import exit
import tomllib


import batchscanner
from batchscanner.credentials import Credentials
from batchscanner.batchscan import run_batch


def parse_args():
    """ Parse command-line arguments
    """

    parser = argparse.ArgumentParser(prog='batchscanner',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-a",
                        dest='action',
                        choices=['scan', 'show', 'script', 'set_tod'],
                        default='scan',
                        help='''Action for batchscanner to take (default: %(default)s). One of: 
                                scan: scan the network and identify which IP address is a Siklu radio;
                                show: extract key metrics from radios (parsed outputs of 'show' commands);
                                script: execute a script: send list of commands read from text file;
                                set_tod: set date and time.''')
    parser.add_argument("-n",
                        dest='network_filename',
                        help="Mandatory filename specifying the Network (range of IP addresses to scan and login credentials). Default: '%(default)s'",
                        default='network.txt')
    parser.add_argument("-c",
                        dest='config_filename',
                        help="Optional configuration file for overriding default program parameters. Default: '%(default)s'",
                        default='config.toml')
    return parser.parse_args()


def main():
    """ A command-line launcher for ``batchscanner``.

        This launcher:

         1. Collects user-configurable parameters via:

             - command-line arguments
             - an optional TOML config file (to override default values)
             - a mandatory file specifying the network (range of IP addresses to scan and login credentials).

         2. Calls the main batchscanner API: :func:`~batchscanner.__main__.run_batch`, with the above parameters.

        Here is a list of parameters that may be included in the optional config file, along with
        their default values:

        =============================  ========  ===========================================================================================================
        Constant                       Defaults  Meaning
        =============================  ========  ===========================================================================================================
        batch_size                     1000      Number of IP addresses in single batch (results saved after each batch)
        script_filename                ''        filename containing list of commands to send to radio (applicable only if action='script')
        include_eh                     true      If true, action EtherHaul radios
        include_bu                     true      If true, action MultiHaul BU radios
        include_tu                     true      If true, action MultiHaul TU radios
        include_tg                     true      If true, action MultiHaul TG radios
        include_tg_remote_cns          false     If true, action all remote CNs (applicable only to TG DNs)
        multiprocessing_flag           true      If true, Run concurrently (much faster running time)
        multiprocessing_num_processes  50        Number of processes to run concurrently
        output_directory               'output'  Results are written to this directory
        save_show_tg_per_radio         false     If true, save also parsed 'show' output per radio (applicable only to TG)
        save_show_tg_per_radio_raw     false     If true, save aso the raw (unparsed) 'show' output per radio (applicable only to TG)
        time_shift                     0         Number of hours to add to computer time when configuring date/time (applicable only if action='set_tod')
        =============================  ========  ===========================================================================================================
    """

    print(f"\nWelcome to {bold('batchscanner')} (ver {batchscanner.__version__}): ", end='')
    print(f"a batch tool for Siklu radios.")
    print(f"Author: {batchscanner.__author__}, 2023.")
    print(f"Documentation: https://batchscanner.readthedocs.io.\n")

    # Parse command-line arguments
    args = parse_args()

    # Parse TOML config file and (where applicable) override default parameters
    filenm = args.config_filename
    _params = {}
    try:
        with open(filenm, 'rb') as fp:
            _params = tomllib.load(fp)
    except FileNotFoundError:
        print(f"Using default program parameters: file '{filenm}' not found")
    except tomllib.TOMLDecodeError as e:
        print(f"Using default program parameters: invalid TOML syntax in '{filenm}':\n{e}")
    else:
        print(f"Updated program parameters from file '{filenm}'")
    finally:
        batch_size = _params.get('batch_size', 1000)
        script_filename = _params.get('script_filename', '')
        include_eh = _params.get('include_eh', True)
        include_bu = _params.get('include_bu', True)
        include_tu = _params.get('include_tu', True)
        include_tg = _params.get('include_tg', True)
        include_tg_remote_cns = _params.get('include_tg_remote_cns', False)
        multiprocessing_flag = _params.get('multiprocessing_flag', True)
        multiprocessing_num_processes = _params.get('multiprocessing_num_processes', 50)
        output_directory = _params.get('output_directory', 'output')
        save_show_tg_per_radio = _params.get('save_show_tg_per_radio', False)
        save_show_tg_per_radio_raw = _params.get('save_show_tg_per_radio_raw', False)
        time_shift = _params.get('time_shift', 0)
    # Ensure at least some radio types are included:
    if not (include_eh or include_bu or include_tu or include_tg):
        print(f"\nTerminating: no radio types included (ensure at least one 'include_xx'",
              f"flag in config file '{args.params_filename}' is set to 'true'")
        exit(0)

    # Parse network file to derive list of IP addresses and username/password
    filenm = args.network_filename
    text_from_filenm = ''
    print(f"Attempting to read range of IP addresses and credentials from file: '{filenm}'")
    try:
        with open(filenm, 'rt') as fp:
            text_from_filenm = fp.read()
    except FileNotFoundError:
        print(f"File not found: '{filenm}'")
    credentials = Credentials(text_to_parse=text_from_filenm)
    len_credentials = len(credentials)
    if len_credentials == 0:
        print(f"\nTerminating: no IP addresses found in file '{filenm}'.")
        exit(0)

    # Read script contents (if required action is to execute script)
    script = []
    if args.action == 'script':
        print(f"Attempting to read script contents from file: {script_filename}")
        try:
            with open(script_filename, 'rt') as fp:
                text_from_filenm = fp.read()
                script = [line.strip() for line in text_from_filenm.split('\n')]
        except FileNotFoundError:
            print(f"File {script_filename} not found.")
        if not script:
            print(f"\nTerminating: no script content.")
            exit(0)

    # Print out summary and final confirmation
    print(f"\nSummary:")
    match args.action:
        case 'scan':
            print(bold("\tAction:\t\tScan"))
        case 'show':
            print(f"\tAction:\t\tShow")
        case 'script':
            print(f"\tAction:\t\tSend script (from file '{script_filename}') with contents:")
            # if script is long, display only top and tail
            if len(script) <= 7:
                commands = script
            else:
                commands = [*script[:3], '...', *script[-3:]]
            for command in commands:
                print(f"\t\t\t\t{command}")
        case 'set_tod':
            print(f"\tAction:\t\tSet date and time based on operating system clock + ({time_shift}) hours")
    print(f"\tNetwork:\t{len_credentials} IP addresses ({credentials[0].ip_addr} - {credentials[-1].ip_addr})")
    if len_credentials > batch_size:
        print(f"\t\t\tin multiple batches, each of {batch_size} IP addresses")
    print(f"\tInclude:")
    if include_eh:
        print(f"\t\t\t- Etherhaul radios")
    if include_bu:
        print(f"\t\t\t- Classic MultiHaul base units (BUs)")
    if include_tu:
        print(f"\t\t\t- Classic MultiHaul terminal units (TUs)")
    if include_tg:
        print(f"\t\t\t- MultiHaul TG radios", end='')
        if include_tg_remote_cns:
            print(f" (with tunneling into remote CNs of each DN - may take longer to run)")
        else:
            print(f" (without tunneling into remote CNs")
    print(f"\tOutput Dir:\t{output_directory}")
    input(f"\nPress enter to launch Batchscanner...\n")
    print("Running...")

    # Run the bot
    run_batch(credentials,
              action=args.action,
              batch_size=batch_size,
              script=script,
              include_eh=include_eh,
              include_bu=include_bu,
              include_tu=include_tu,
              include_tg=include_tg,
              include_tg_remote_cns=include_tg_remote_cns,
              multiprocessing_flag=multiprocessing_flag,
              multiprocessing_num_processes=multiprocessing_num_processes,
              output_directory=output_directory,
              save_show_tg_per_radio=save_show_tg_per_radio,
              save_show_tg_per_radio_raw=save_show_tg_per_radio_raw,
              time_shift=time_shift
              )
    print(f"\nBatchscanner terminated. Results saved in directory '{output_directory}'.")
    return None


def bold(txt: str) -> str:
    """ Return `txt` with ANSI escape codes for bold typeface

    """
    return f"\033[1m{txt}\033[0m"


if __name__ == '__main__':
    # Required by the Python Multiprocessing Pool framework
    multiprocessing.freeze_support()
    main()

