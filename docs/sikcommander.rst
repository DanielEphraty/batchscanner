SikCommander: CLI commander
=====================================

``sikcommander.py`` implements :class:`~batchscanner.sikcommander.SikCommander`: a CLI commander
for high-level management of CLI session with a Siklu radio. It provides the following functionality:

 #. Manage a CLI session with a radio (a wrapper for :class:`~batchscanner.sikcli.SikCli`)
 #. Run 'show' CLI commands and parse the output
 #. Perform actions, such as:

     - setting the time of day
     - executing a script (list of commands)

SikCommander makes use of auxiliary modules to parse the output of 'show' CLI commands:

 * :doc:`parsers.parse_show_eh <parse_show_eh>`: for EtherHaul and (classic) MultiHaul radios
 * :doc:`parsers.parse_show_tg <parse_show_eh>`: for MultiHaul TG radios.

It also makes use of :class:`~batchscanner.credentials.Credential` as a container for
radio's IP address, username, and password.

Usage Examples:
----------------------

.. code-block::
   :caption: MH-TG Radio
   
   >>> from batchscanner.credentials import Credential
   >>> credential = Credential('192.168.0.1', 'admin', 'admin')
   >>> from batchscanner.sikcommander import SikCommander
   >>> commander = SikCommander(credential, include_tg_remote_cns=True)
   >>> commander.show_tg()
   >>> print(commander)
   SikCommander:
      credential: Credential(192.168.0.1, admin, admin)
      include_tg_remote_cns: True
      connected: True
      errors: []
      model: MH-N366
      name: dn1
      radio_type: TG
      sw: 
      sn: 
      tg_remote_cns: ['cn1', 'cn2', 'cn3']
      commands_sent: [SikCommand(command=show radio-common, target_id=192.168.0.1: dn1, success=True, response='radio-bridge-tg-radio-common:radio-common...),
                      SikCommand(command=show radio-dn, target_id=192.168.0.1: dn1, success=True, response='radio-bridge-tg-radio-dn:radio-dn {\r\nnode-c...),
                      SikCommand(command=show, target_id=192.168.0.1: dn1, success=True, response='ietf-netconf-acm:nacm {\r\n   enable-nacm true;\r\n  '...),
                      SikCommand(command=show, target_id=192.168.0.1: dn1 -> cn1, success=True, response='ietf-netconf-acm:nacm {\r\n   enable-nacm true;...),
                      SikCommand(command=show, target_id=192.168.0.1: dn1 -> cn2, success=True, response='ietf-netconf-acm:nacm {\r\n   enable-nacm true;...),
                      SikCommand(command=show, target_id=192.168.0.1: dn1 -> cn3, success=True, response='ietf-netconf-acm:nacm {\r\n   enable-nacm true;...)
                     ]
      output: [SikShowTg: parsed show output for '192.168.0.1: dn1',
               SikShowTg: parsed show output for '192.168.0.1: dn1 -> cn1',
               SikShowTg: parsed show output for '192.168.0.1: dn1 -> cn2',
               SikShowTg: parsed show output for '192.168.0.1: dn1 -> cn3'
              ]
 

.. code-block::
   :caption: EH / (classic) MH
   
   >>> from batchscanner.credentials import Credential
   >>> credential = Credential('192.168.0.1', 'admin', 'admin')
   >>> from batchscanner.sikcommander import SikCommander
   >>> commander = SikCommander(credential)
   >>> commander.set_tod()
   >>> _ = commander.send_cmds(['set system location London','set system contact Daniel'])
   >>> print(commander)
   SikCommander:
        credential: Credential(192.168.0.1, admin, admin)
        include_tg_remote_cns: False
        connected: True
        errors: []
        model: EH-710TX
        name: EH-710TX
        radio_type: EH
        sw: 7.7.10-13186-d2f25a6
        sn: T.BJF94A0015
        tg_remote_cns: []
        commands_sent: [SikCommand(command=set system time 07:15:52, target_id=192.168.180.23: EH-710TX, success=True, response='Set done: system '),
                        SikCommand(command=set system date 2023.08.16, target_id=192.168.180.23: EH-710TX, success=True, response='Set done: system '),
                        SikCommand(command=set system location London, target_id=192.168.180.23: EH-710TX, success=True, response='Set done: system '),
                        SikCommand(command=set system contact Daniel, target_id=192.168.180.23: EH-710TX, success=True, response='Set done: system ')
                       ]
        output: []



Class Information:
------------------

.. autoclass:: batchscanner.sikcommander.SikCommander

.. autoclass:: batchscanner.sikcommander.SikCommand
   :no-special-members:


