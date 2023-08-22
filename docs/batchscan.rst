Batchscan: batch engine
========================

``batchscan.py`` implements the main API for batchscanner: :func:`~batchscanner.batchscan.run_batch`.
Calling this function accomplishes the following:

#. Loop over all devices in a user-defined IP-address space. This space is represented
   as :class:`~batchscanner.credentials.Credentials`.

#. For each device, launch :func:`~batchscanner.batchscan.worker_task`: essentially a wrapper
   for :class:`~batchscanner.sikcommander.SikCommander`.

#. When all worker tasks are complete, results are saved using class: :class:`~batchscanner.batchscan.WriteResults`.

Because the IP address space may be very large, a facility provided to process them in *batches*, where (partial)
results are saved after each batch completes. Multiple batches have an overhead on execution time
(because results are saved multiple times per batch), but are 'safer' in that not all results are lost if the
program crashes.

Usage Examples:
----------------------

.. code-block::

   >>> from batchscanner.credentials import Credentials
   >>> network = Credentials(text_to_parse='192.168.0.0/24')
   >>> from batchscanner.batchscan import run_batch
   >>> run_batch(network)
   Batch 0 at 20230816_071146: 254 Credentials: from 192.168.0.1 to 192.168.0.254
        Checking 192.168.0.1
        Checking 192.168.0.2
        ...
        Checking 192.168.0.254
   >>> from pathlib import Path
   >>> results_file = next(Path('output').glob('*scan*'))
   >>> print(results_file.read_text())
   ip_addr,       radio_type, model,     name,     sw,     sn,           last_non_cmd_error
   192.168.0.1,     ,                 ,          ,       ,             , Socket timeout
   192.168.0.2,   EH,         EH-710TX,  EH-710TX, 7.7.10, T.BJF943017B,
   192.168.0.3,   EH,         EH-600TX,  EH-600TX, 7.7.12, T.BJF7CC00D7,
   ...
   192.168.0.253,   ,                 ,          ,       ,             , Authentication failed
   192.168.0.254,   ,                 ,          ,       ,             , Connection refused to port 22

Function Information:
-----------------------

.. autofunction:: batchscanner.batchscan.run_batch

.. autofunction:: batchscanner.batchscan.worker_task

Class Information:
-----------------------

.. autoclass:: batchscanner.batchscan.WriteResults


