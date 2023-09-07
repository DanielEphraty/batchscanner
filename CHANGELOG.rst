Version 0.1.5 (07/09/2023)
--------------------------

* ``sikcli.py``:

    - Sped up waiting on responses to commands. Instead of timing out on response_timeout, continuously analyse response
      *incrementally*, to determine when completed
    - As a consequence, response_timeout in sikssh_config.toml no longer has any effect
    - Improved reliability of tunnel_in() and tunnel_out()



Version 0.1.4 (25/08/2023)
--------------------------

 * A single source of truth for version (in batchscanner.__init__.py)

 * Added this CHANGELOG.rst file and incorporated into documentation

 * ``sikcommander.py``:

    - Added timestamp to sikcommander.Command
    - in SikCommander.__init__, reading remote CNs now conditioned also on SikCommander.connected

 * ``credentials.py``:

    - made :class:`~batchscanner.credentials.Credential` hashable
    - changed :class:`~batchscanner.credentials.Credentials` so it automatically filters out any duplicate IP addresses

* ``sikcli.py``:

    - Try to extract banner (and derive related parameters) even if authentiction fails
    - To faciliate above: No longer call _derive_model() from within disconnect()

* ``batchscan.py``: actions in worker_task() now conditioned on SikCommander.connected
