Synopsis
========================

Batchscanner is a program to batch-query or batch-configure multiple Siklu radios
via their CLI (SSH) interface.

.. note::
   This program is a personal contribution. It is not affiliated with `Siklu Communications <https://www.siklu.com>`_
   in any way, and does not contain any Siklu proprietary and/or confidential information.

The main API is the function :func:`batchscan.run_batch`, and a working example launcher for this API
is provided in :mod:`__main__`. Results are written to text and/or csv files.

Batchscanner is built in 4 layers:
 #. A low-level CLI session manager for Siklu radios: *sikssh.py*, with main API
    class: :class:`batchscanner.sikcli.SikCli`. Instantiating this class creates
    an SSH session to a radio, and derives basic radio details via the SSH banner/prompt. Methods are provided
    to send commands, and to tunnel into remote radios (relevant for MultiHaul TG radios).
    Comprehensive logging is provided by default.
	
 #. A CLI commander: *sikcommander.py*, with main API class: :class:`batchscanner.sikcommander.SikCommander`.
    This is a wrapper for :class:`batchscanner.sikcli.SikCli`, providing additional functionality, such as:
    - parsing the output of the 'show' command
    - executing an action, such as setting the time of day, or executing a script (list of commands).

 #. A 'bot' that performs some action across all devices in a user-defined IP address space: *batchscan.py*,
    with main API function:  :func:`batchscanner.batchscan.run_batch`.
    This 'bot' launches :class:`batchscanner.sikcommander.SikCommander` for each device,
    in order to perform some user-defined action. :mod:`batchscanner.batchscan` also contains
    :class:`batchscanner.batchscan.WriteResults` which saves the results into files.

 #. Next item

