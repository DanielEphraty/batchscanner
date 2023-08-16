""" The main API for the batch CLI scanner
"""
import csv
import datetime
import multiprocessing
from pathlib import Path
from typing import Iterator

from batchscanner.sikcommander import SikCommander
from batchscanner.sikcredentials import SikCredentials
from batchscanner.parsers.parse_show_tg import SikShowTg


class WriteResults:
    """ A collection of functions for saving the scan results in multiple text files.
    """

    def __init__(self, *,
                 dir_output_name: str = 'output',
                 dir_show_tg_per_radio_name: str = 'show_tg_per_radio',
                 dir_show_tg_per_radio_raw_name: str = 'show_tg_per_radio_raw',
                 filenm_scan: str = 'scan_results.csv',
                 filenm_cmds: str = 'cmds_results.csv',
                 filenm_show_eh: str = 'show_eh.csv',
                 filenm_show_bu: str = 'show_bu.csv',
                 filenm_show_tu: str = 'show_tu.csv',
                 filenm_show_tg_interfaces: str = 'show_tg_interfaces.csv',
                 filenm_show_tg_inventory: str = 'show_tg_inventory.csv',
                 filenm_show_tg_ip: str = 'show_tg_ip.csv',
                 filenm_show_tg_links: str = 'show_tg_links.csv',
                 filenm_show_tg_node: str = 'show_tg_node.csv',
                 filenm_show_tg_sectors: str = 'show_tg_sectors.csv',
                 filenm_show_tg_system: str = 'show_tg_system.csv',
                 filenm_errors: str = 'errors.csv',
                 save_show_tg_per_radio: bool = True,
                 save_show_tg_per_radio_raw: bool = False,
                 ):
        """

        :param dir_output_name: Name of the directory into which results are written
        :param dir_show_tg_per_radio_name: Name of directory into which *show* results for individual TG radios
                                           are written. Applicable only if `save_show_tg_per_radio` == True.
        :param dir_show_tg_per_radio_raw_name: Name of directory into which raw *show* output for individual TG radios
                                               are written. Applicable only if `save_show_tg_per_radio_raw` == True.
        :param filenm_scan: Output filename for scan results.
        :param filenm_cmds: Output filename for script results.
        :param filenm_show_eh: Output filename for show results of EH radios.
        :param filenm_show_bu: Output filename for show results of BU radios.
        :param filenm_show_tu: Output filename for show results of TU radios.
        :param filenm_show_tg_interfaces: Output filename for show results of TG radios: **interfaces** section.
        :param filenm_show_tg_inventory: Output filename for show results of TG radios: **inventory** section.
        :param filenm_show_tg_ip: Output filename for show results of TG radios: **ip** section.
        :param filenm_show_tg_links: Output filename for show results of TG radios: **links** section.
        :param filenm_show_tg_node:  Output filename for show results of TG radios: **node** section.
        :param filenm_show_tg_sectors:  Output filename for show results of TG radios: **sectors** section.
        :param filenm_show_tg_system:  Output filename for show results of TG radios: **system** section.
        :param filenm_errors: Output filename for errors
        :param save_show_tg_per_radio: Applicable to TG radios only: If True, save the output of 'show' for
                                       individual radios.
        :param save_show_tg_per_radio_raw: Applicable to TG radios only: If True, save the raw dump output of
                                           'show' for individual radios.
        """
        self.dirname_output = dir_output_name
        self.dirname_show_tg_per_radio = dir_show_tg_per_radio_name
        self.dirname_show_tg_per_radio_raw = dir_show_tg_per_radio_raw_name
        self.filenm_scan = filenm_scan
        self.filenm_cmds = filenm_cmds
        self.filenm_show_eh = filenm_show_eh
        self.filenm_show_bu = filenm_show_bu
        self.filenm_show_tu = filenm_show_tu
        self.filenm_show_tg_interfaces = filenm_show_tg_interfaces
        self.filenm_show_tg_inventory = filenm_show_tg_inventory
        self.filenm_show_tg_ip = filenm_show_tg_ip
        self.filenm_show_tg_links = filenm_show_tg_links
        self.filenm_show_tg_node = filenm_show_tg_node
        self.filenm_show_tg_sectors = filenm_show_tg_sectors
        self.filenm_show_tg_system = filenm_show_tg_system
        self.filenm_errors = filenm_errors
        self.save_show_tg_per_radio = save_show_tg_per_radio
        self.save_show_tg_per_radio_raw = save_show_tg_per_radio_raw
        self.prefix = ''
        #
        # Prepare output directories
        self.dir_output = Path(self.dirname_output)
        if not self.dir_output.is_dir():
            self.dir_output.mkdir(parents=True)
        if self.save_show_tg_per_radio:
            self.dir_show_tg_per_radio = self.dir_output / self.dirname_show_tg_per_radio
            if not self.dir_show_tg_per_radio.is_dir():
                self.dir_show_tg_per_radio.mkdir(parents=True)
        if self.save_show_tg_per_radio_raw:
            self.dir_show_tg_per_radio_raw = self.dir_output / self.dirname_show_tg_per_radio_raw
            if not self.dir_show_tg_per_radio_raw.is_dir():
                self.dir_show_tg_per_radio_raw.mkdir(parents=True)

    def write_csv(self, records: Iterator[dict], filename: str) -> int:
        """ Write csv file `filename` where each row is an item (dictionary) in `records`

            :params records: An iterator of dictionaries, where each dictionary should have the same
                             keys. The csv header row (specifying field names) is derived from the
                             first element in `records`.
            :type records: Iterator[dict]
            :param filename: Filename for output csv file.
            :type filename: str
            :return: number of records (items) written to `filename`.
            """

        records_written = 0
        try:
            first_record = next(records)
        except StopIteration:
            return records_written
        else:
            fieldnames = first_record.keys()
            fp = self.dir_output / f"{self.prefix}_{filename}"
            with open(fp, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerow(first_record)
                records_written += 1
                for record in records:
                    writer.writerow(record)
                    records_written += 1
            return records_written

    def write_show_tg(self, results: Iterator[SikShowTg]):
        """ Write the output of 'show' command for TG radios by section.

        :param results: An iterator of...
        :return:
        """
        # keys correspond to the SikShowTg output attributes. Values correspond to filenames
        section_filenames = {'interfaces': self.filenm_show_tg_interfaces,
                             'inventory': self.filenm_show_tg_inventory,
                             'ip': self.filenm_show_tg_ip,
                             'links': self.filenm_show_tg_links,
                             'node': self.filenm_show_tg_node,
                             'sectors': self.filenm_show_tg_sectors,
                             'system': self.filenm_show_tg_system,
                             }
        file_handles = {}
        for result in results:
            if self.save_show_tg_per_radio:
                fp = self.dir_show_tg_per_radio / f"{self.prefix}_show_tg_{result.name}.txt"
                with open(fp, 'wt') as f:
                    f.write(str(result))
            if self.save_show_tg_per_radio_raw:
                fp = self.dir_show_tg_per_radio_raw / f"{self.prefix}_show_tg_raw_{result.name}.txt"
                with open(fp, 'wt') as f:
                    f.write(result.show_dump.replace('\r', ''))
            for section, filenm in section_filenames.items():
                try:
                    header, data = getattr(result, section).tocsv()
                except AttributeError:
                    continue
                else:
                    if not file_handles.get(section):
                        file_path = self.dir_output / f"{self.prefix}_{filenm}"
                        file_handles[section] = open(file_path, 'wt')
                        file_handles[section].write(header)
                    file_handles[section].write(data)
        for handle in file_handles.values():
            handle.close()


def worker_task(params):
    """ A single worker task specified by `params`:
        1. Extract parameters packed into dict 'params`.
        2. Create an instance of :class:`sikcommander.SikCommander`.
        3. Call the appropriate instance method based on the specified `action` and `include_xx` flags.
        4. return the instance

    :param params: A dictionary containing parameters required by worker task.
                   Keys are: `action`, `script`, `credential`,
                   `include_eh`, `include_bu`, `include_tu`, `include_tg`, `include_tg_remote_cns`,
                   and `time_shift`. These are documented in :func:`run_scan`.
    :type params: dict
    :return: SikCommander
    """

    # Extract individual parameters from function argument params
    action = params['action']
    commands = params['script']
    credential = params['credential']
    include_bu = params['include_bu']
    include_eh = params['include_eh']
    include_tg = params['include_tg']
    include_tg_remote_cns = params['include_tg_remote_cns']
    include_tu = params['include_tu']
    time_shift = params['time_shift']
    # Start SikCommander
    print(f"\tChecking {str(credential.ip_addr)}")
    commander = SikCommander(credential, include_tg and include_tg_remote_cns)
    match action:
        case 'scan':
            pass  # no need to do anything else
        case 'show':
            if commander.radio_type == 'EH' and include_eh:
                commander.show_eh()
            if commander.radio_type == 'BU' and include_bu:
                commander.show_bu()
            if commander.radio_type == 'TU' and include_tu:
                commander.show_tu()
            if commander.radio_type == 'TG' and include_tg:
                commander.show_tg()
        case 'script':
            if commander.radio_type == 'EH' and include_eh:
                commander.send_cmds(commands)
            if commander.radio_type == 'BU' and include_bu:
                commander.send_cmds(commands)
            if commander.radio_type == 'TU' and include_tu:
                commander.send_cmds(commands)
            if commander.radio_type == 'TG' and include_tg:
                commander.send_cmds(commands)
                if commander.include_tg_remote_cns:
                    commander.send_cmds_remote_cns(commands)
        case 'set_tod':
            if commander.radio_type == 'EH' and include_eh:
                commander.set_tod(time_shift)
            if commander.radio_type == 'BU' and include_bu:
                commander.set_tod(time_shift)
            if commander.radio_type == 'TU' and include_tu:
                commander.set_tod(time_shift)
            if commander.radio_type == 'TG' and include_tg:
                commander.set_tod_tg(time_shift)
    del commander.cli
    return commander


def run_scan(credentials: SikCredentials, *,
             action: str = 'scan',
             batch_size: int = 1000,
             script: list[str] | None = None,
             include_eh: bool = True,
             include_bu: bool = True,
             include_tu: bool = True,
             include_tg: bool = True,
             include_tg_remote_cns: bool = True,
             multiprocessing_flag: bool = True,
             multiprocessing_num_processes: int = 50,
             output_directory: str = 'output',
             save_show_tg_per_radio: bool = True,
             save_show_tg_per_radio_raw: bool = False,
             time_shift: float = 0,
             ) -> None:
    """ The top-level API for running the batch CLI scanner. It performs the following:

        1. Loop over all IP addresses (as defined in :attr:`credentials`) in *batches*.
           Each batch includes :attr:`batch_size` IP addresses. Results are saved to file(s) after each batch
           finishes running. The next batch (if any) then proceeds.
        2. For each IP address (in a batch), :func:`worker_task` is launched. These worker tasks are typically
           run under the
           `Multiprocessing Pool <https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool>`_
           framework. The worker tasks can be called sequentially (as a single process)
           by setting :attr:`multiprocessing_flag` to False.
        3. Once all worker tasks return their results for the batch, results are saved into file(s)
           under the :attr:`output_directory` directory. All filenames are prepended with a timestamp to avoid
           file management issues.

        .. warning:: In order to successfully use this function under the Multiprocessing Pool framework,
                     The statement: **multiprocessing.freeze_support()**
                     must be included as the first statement under *__main__* section of the calling script.

        :param credentials: A sequence of :class:`SikCredential`, each designating an IP address and log-in credentials
                            to a Siklu radio
        :type credentials: SikCredentials
        :param action: The action to be taken by the bot. One of:
                       '**scan**': identify Siklu radios;
                       '**show**': extract key metrics from radios;
                       '**script**': execute sequence of commands read from text file;
                       '**set_tod**': set date and time.
        :type action: str
        :param batch_size: Number of IP addresses comprising a single batch.
                           Batches are run sequentially, with results saved to file once a batch completes.
                           Smaller batches therefore have larger overheads, but are
                           less prone to losing a lot of information if the program crashes.
        :type batch_size: int
        :param script: Applicable only if `action` =='command': list of commands to send to radio.
        :type script: list[str]
        :param include_eh: If True, the bot operates on EtherHaul radios
        :type include_eh: bool
        :param include_bu: If True,the bot operates on (classic) MultiHaul BU radios
        :type include_bu: bool
        :param include_tu: If True, the bot operates on (classic) MultiHaul TU radios
        :type include_tu: bool
        :param include_tg: If True, the bot operates on MultiHaul TG radios
        :type include_tg: bool
        :param include_tg_remote_cns: Applicable to MultiHaul TG radios only: if True, `action` is
                                      applied to remote CNs (if any). Often remote CNs do not have unique
                                      IP addresses, so this is the only way to access them.
        :type include_tg_remote_cns: bool
        :param multiprocessing_flag: If True, instances of :func:`worker_task` in each batch are launched under the
                                     `Multiprocessing Pool <https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool>`_
                                     framework. If False, :func:`worker_task` are launched sequentially (single process)
                                     which may take a very long time to run.
        :param multiprocessing_num_processes: The number of worker processes to used if `mutiprocessing_flag` == True.
        :type multiprocessing_num_processes: int
        :type multiprocessing_flag: bool
        :param output_directory: Name of the directory into which results are written.
        :type output_directory: str
        :param save_show_tg_per_radio: Applicable only to MultiHaul TG radios: Results of the *show* :attr:`action`
                                       are grouped under 'topic files' (e.g.: 'system', 'links', etc.), where each file
                                       includes results for all radios in a batch. If this flag is True, information
                                       extracted from *show* are saved also per radio.
        :type save_show_tg_per_radio: bool
        :param save_show_tg_per_radio_raw: Applicable to MultiHaul TG radios only: Controls if the raw output of
                                           the *show* command are saved (per radio).
        :type save_show_tg_per_radio_raw: bool
        :param time_shift: Applicable only to `action` == 'set_tod': designates the time shift between computer time
                           and the time that will be configured to the radios. For example: if computer time is 13:00,
                           and :attr:`time_shift` equals 2.5, then the time configured to radio is 15:30.
                           This is useful in cases where the computer is not located in the same timezone as the radios.
        :type time_shift: float

        :return: None.
    """

    # Pack parameters required by worker_task()
    params = {k: v for k, v in locals().items() if k in ['action',
                                                         'script',
                                                         'include_bu',
                                                         'include_eh',
                                                         'include_tg',
                                                         'include_tg_remote_cns',
                                                         'include_tu',
                                                         'time_shift',
                                                         ]}
    # Loop over batches
    for batch_num, batch in enumerate(credentials.get_batches(batch_size)):
        print(f"Batch {batch_num} at {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}: {batch}")
        worker_params = [{'credential': credential, **params} for credential in batch]
        if multiprocessing_flag:
            with multiprocessing.Pool(processes=multiprocessing_num_processes) as pool:
                results = pool.map(worker_task, worker_params)
        else:
            results = list(map(worker_task, worker_params))
        # Write results
        wr = WriteResults(dir_output_name=output_directory,
                          save_show_tg_per_radio=save_show_tg_per_radio,
                          save_show_tg_per_radio_raw=save_show_tg_per_radio_raw,
                          )
        wr.prefix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        # Write scan results
        r = (result.as_dict() for result in results)
        wr.write_csv(r, wr.filenm_scan)
        if action != 'scan':
            # Write script results
            r = (cmd.as_dict() for result in results for cmd in result.commands_sent)
            wr.write_csv(r, wr.filenm_cmds)
            # Write show results for EH
            r = (result.output[0] for result in results if (result.radio_type == 'EH' and result.output))
            wr.write_csv(r, wr.filenm_show_eh)
            # Write show results for BU
            r = (result.output[0] for result in results if (result.radio_type == 'BU' and result.output))
            wr.write_csv(r, wr.filenm_show_bu)
            # Write show results for TU
            r = (result.output[0] for result in results if (result.radio_type == 'TU' and result.output))
            wr.write_csv(r, wr.filenm_show_tu)
            # Write show results for TG
            r = (item for result in results if result.radio_type == 'TG' for item in result.output)
            wr.write_show_tg(r)

