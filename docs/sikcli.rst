SikCli: low-level CLI manager
==============================

SikCli is a low-level class for managing CLI sessions with a Siklu radio (implemented in
``sikcli.py``). It essentially wraps
`Paramiko <https://docs.paramiko.org/en/stable/index.html>`_, customising it for the Siklu CLI.

.. note::
   Applications would not usually call SikCli directly, but rather
   through the wrapper class :class:`~batchscanner.sikcommander.SikCommander`.

Usage Examples:
----------------------

.. code-block::
   :caption: MH-TG Radio

   >>> from batchscanner.sikcli import SikCli
   >>> cli = SikCli('192.168.0.1', username='admin', password='admin')
   >>> print(ssh)
   SikCli 	ip_addr: 192.168.0.1
		username: admin
		password: admin
		connected: True
		banner: 
		model: MH-N366
		sn: 
		sw: 
		prompt: MH-N366@dn1>
		name: dn1
		last_err: 
   >>> cli.tunnel_in('dn2')
   >>> cli.tunnel_in('dn3')
   >>> print(cli.name, cli.tunnel_stack)
   dn3 ['dn1', 'dn2']
   >>> cli.disconnect()

.. code-block::
   :caption: EH / (classic) MH
   
   >>> from batchscanner.sikssh import SikCli
   >>> cli = SikCli('192.168.0.1', username='admin', password='admin')
   >>> print(cli)
   SikCli	ip_addr: 192.168.0.1
		username: admin
		password: admin
		connected: True
		banner: EH-1200F, S/N: F544140339, Ver: 7.7.12-13214-f614d18
		model: EH-1200F
		sn: F544140339
		sw: 7.7.12-13214-f614d18
		prompt: radio_name>
		name: radio_name
		last_err: 
   >>> response = cli.send('show system snmpid')
   >>> print(response)
   system snmpid            : .1.3.6.1.4.1.31926
   >>> cli.disconnect()



Class Information:
------------------

.. autoclass:: batchscanner.sikcli.SikCli







