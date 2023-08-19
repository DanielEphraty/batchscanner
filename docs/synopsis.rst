Synopsis
========================

:program:`Batchscanner` is a program to batch-query or batch-configure multiple Siklu radios
via their CLI (SSH) interface.

The main API is the function :func:`batchscanner.batchscan.run_batch`, and a command-line launcher for this API
is provided in :mod:`batchscanner.__main__`. Results are written to text and/or csv files.

Batchscanner is built in 4 layers:
 #. A **low-level CLI session manager** for Siklu radios: ``sikssh.py``, with main API
    class: :class:`~batchscanner.sikcli.SikCli`. Instantiating this class creates
    an SSH session to a radio, and derives basic radio details via the SSH banner/prompt. Methods are provided
    to send commands, and to tunnel into remote radios (relevant for MultiHaul TG radios).
    Comprehensive logging is provided by default.

    For in-depth information, refer to: :doc:`sikcli`.
	
 #. A **CLI commander**:``sikcommander.py``, with main API class: :class:`~batchscanner.sikcommander.SikCommander`.
    This is a wrapper for :class:`~batchscanner.sikcli.SikCli`, providing additional functionality, such as:

     - parsing the output of the 'show' command
     - executing an action, such as setting the time of day, or executing a script (list of commands).

    For in-depth information, refer to: :doc:`sikcommander`.

 #. A **batch engine**: ``batchscan.py``, with main API function: :func:`~batchscanner.batchscan.run_batch`.
    It executes some action by invoking :class:`~batchscanner.sikcommander.SikCommander`
    across all devices in a user-defined IP address space.
    It also implements class :class:`~batchscanner.batchscan.WriteResults` which saves the results into files.

    For in-depth information, refer to: :doc:`batchscan`.

 #. A **command-line launcher**: ``__main__.py``. It:

    a. Collects user-configurable parameters via:

         - command-line arguments
         - an optional TOML config file (to override default values)
         - a mandatory file specifying the network (range of IP addresses to scan and login credentials).

    b. Calls the main batch engine API: :func:`~batchscanner.batchscan.run_batch`, with the above parameters.

    For in-depth information, refer to: :doc:`quick_start`.


