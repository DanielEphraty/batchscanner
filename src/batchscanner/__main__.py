""" A working example launcher for batchscanner """

import argparse
from importlib import resources
import multiprocessing
import tomllib

import batchscanner
from batchscanner.credentials import Credentials
from batchscanner.batchscan import run_batch


def bold(txt: str) -> str:
    """ Return `txt` with ANSI escape codes for bold typeface
    """
    return f"\033[1m{txt}\033[0m"


def parse_args():
    """ Parse command-line arguments
    """

    parser = argparse.ArgumentParser(prog='batchscanner',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-a",
                        dest='action',
                        choices=['scan', 'show', 'script', 'set_tod'],
                        default='show',
                        help='''Action for batchscanner to take (default: %(default)s). One of: 
                                scan: scan the network and identify which IP address is a Siklu radio;
                                show: extract key metrics from radios (parsed outputs of 'show' commands);
                                script: execute a script: send list of commands read from text file;
                                set_tod: set date and time.''')
    parser.add_argument("-n",
                        dest='network_filename',
                        help="Filename specifying the Network (range of IP addresses to scan and login credentials). Default: '%(default)s'",
                        default='network.txt')
    parser.add_argument("-c",
                        dest='config_filename',
                        help="Configuration file for overriding default program parameters. Default: '%(default)s'",
                        default='config.toml')
    return parser.parse_args()


def main():
    """ An example command-line wrapper for launching `:func:batchscan.runscan`. This  wrapper:
        1. Collects user-configurable parameters via:
            - command-line arguments
            - an optional TOML parameter file (to override default values)
            - a mandatory file specifying the Network (range of IP addresses to scan and login credentials).
        2. Calls the main batchscanner API: `func:batchscan.runscan`, with the above parameters.
    """

    print(f"\nWelcome! This is a launcher for {bold('batchscan')} (ver {batchscanner.__version__}): ", end='')
    print(f"a batch tool for Siklu radios.")
    print(f"Author: {batchscanner.__author__}, 2023.\n")

    # Parse command-line arguments
    args = parse_args()

    # Parse TOML config file and override default parameters
    filenm = args.config_filename
    _params = {}
    try:
        _params = tomllib.loads(resources.files('batchscanner').joinpath(filenm).read_text())
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
        text_from_filenm = resources.files('batchscanner').joinpath(filenm).read_text()
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
            text_from_filenm = resources.files('batchscanner').joinpath(script_filename).read_text()
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
    input(f"\nPress enter to launch the CLI bot...\n")
    print("Running...")

    # Run the bot
    run_batch(credentials,
              action=args.action,
              batch_size=batch_size,
              script=script,
              include_bu=include_bu,
              include_eh=include_eh,
              include_tg=include_tg,
              include_tg_remote_cns=include_tg_remote_cns,
              include_tu=include_tu,
              multiprocessing_flag=multiprocessing_flag,
              multiprocessing_num_processes=multiprocessing_num_processes,
              output_directory=output_directory,
              save_show_tg_per_radio=save_show_tg_per_radio,
              save_show_tg_per_radio_raw=save_show_tg_per_radio_raw,
              time_shift=time_shift
              )
    print(f"\nCLI Bot terminated. Results saved in directory '{output_directory}'.")


if __name__ == '__main__':
    # Required by the Python Multiprocessing Pool framework
    multiprocessing.freeze_support()
    main()
