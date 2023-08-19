Parser for MultiHaul TG Radios
===================================

The output of a TG 'show' command takes some effort to parse and tokenise. The module *parse_show_tg.py*
is dedicated to doing just this. The main API is class :class:`~batchscanner.parsers.parse_show_tg.SikShowTg`.
For further information, refer to `Implementation Details`_.

Usage Example
--------------

.. code-block::
   :caption: Trivial example

   >>> from batchscanner.sikcli import SikCli
   >>> cli = SikCli('192.168.0.1', username='admin', password='admin')
   >>> show_dump = cli.send('show')

   >>> from batchscanner.parsers.parse_show_tg import SikShowTg
   >>> tokens = SikShowTg(show_dump, 'TG @192.168.0.1')
   >>> tokens
   Interfaces:
   name      port    status    dup    speed
   dn1       eth1    up        FD     1Gbps
   dn1       eth2    down
   dn1       eth3    down

   IP:
   name      address        pref    vlan    gateway
   dn1       192.168.0.1    24              192.168.0.100

   Inventory:
   name      sn          model                hw_rev    sw_ver
   dn1       FB18483274  MH-N366-CCP-PoE-MWB  A1        1.3.1-2436

   Node:
   name      popdn    sync               mode    sched    ptx    freq    pol    gol
   dn1       False    gps-sync-holdover  BU      Long     auto   60480   even   1|1

   Sectors:
   name      sec    admin    cfg_f    pol    gol    act_f       sync      Tmdm    Trf
   dn1       1      up       60480    even   1|1    60480 (ok)  internal  50      45
   dn1       2      up       64800    even   1|1    64800 (ok)  internal  49      50
   dn1       3      up       60480    even   1|1    60480 (ok)  internal  50      49
   dn1       4      up       64800    even   1|1    64800 (ok)  internal  50      52

   Links:
   name      remote    admin    role    status        uptime         type    cfg_lsec    cfg_rsec    act_lsec    act_rsec    rssi    snr    mcs_tx    mcs_rx
   dn1       cn1       up       init    up            00051:29:54:34 cn      3           1           3           1           -65     11     9         10

   System:
   name      product    uptime          datetime             location    sw_active    sw_passive    gps_mode    gps_sats
   dn1       MH-N366    00055:07:55:38  2023-08-17 06:30:32  London      1.3.1        2.1.2         3D          11

SikShowTg Class Information
----------------------------
.. autoclass:: batchscanner.parsers.parse_show_tg.SikShowTg


Implementation Details
-----------------------

Parsing
^^^^^^^^^

Parsing the output of a TG 'show' command is implemented in
method :meth:`~batchscanner.parsers.parse_show_tg.SikShowTg._deyamlify`.
In a nutshell, it converts the output into a standard YAML, and then uses a standard
YAML parser to convert int a a list of dictionaries.

_deyamlify Class Information
"""""""""""""""""""""""""""""

.. automethod:: batchscanner.parsers.parse_show_tg.SikShowTg._deyamlify

Tokenising
^^^^^^^^^^^

The key *attributes* of class :class:`~batchscanner.parsers.parse_show_tg.SikShowTg` are
each an instance of class :class:`~batchscanner.parsers.parse_show_tg.SikShowTgSection`:
essentially a container for one or more *atoms* of the same types.

*Atoms* are class instances for storing tokensied
data for specific section of the output of the 'show' command. For example,
:class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomLink` contains tokens pertaining to the
'radio-dn links' and 'radio-common links' sections of the 'show' output. There may be
multiple instances of :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomLink`
(grouped in container :class:`~batchscanner.parsers.parse_show_tg.SikShowTgSection`,
each corresponding to a different configured link).

SikShowTgSection Class Information
""""""""""""""""""""""""""""""""""""

.. autoclass:: batchscanner.parsers.parse_show_tg.SikShowTgSection

Atoms
"""""""""""""""""""""""""""""

The different types of *atoms* are subclasses of :class:`~batchscanner.parsers.parse_show_tg.TgShowAtom`,
which provide convenient functions, such as converting an atom to csv.

The following table shows the correspondence between the attributes
of :class:`~batchscanner.parsers.parse_show_tg.SikShowTg`, and the
type of *atoms* they contain.

.. table:: Atom classes within the main :class:`~batchscanner.parsers.parse_show_tg.SikShowTg` Attributes

   ==================================================================   ====================================================================
   SikShowTg Attribute                                                  Atoms contained within the SikShowTgSection
   ==================================================================   ====================================================================
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.interfaces`     :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomInterface`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.inventory`      :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomInventory`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.ip`             :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomIp`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.links`          :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomLink`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.node`           :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomNode`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.sectors`        :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomSector`
   :attr:`~batchscanner.parsers.parse_show_tg.SikShowTg.system`         :class:`~batchscanner.parsers.parse_show_tg.SikShowTgAtomSystem`
   ==================================================================   ====================================================================

SikShowTgAtom* Classes Information
""""""""""""""""""""""""""""""""""""

.. automodule:: batchscanner.parsers.parse_show_tg
   :no-special-members:
   :exclude-members: SikShowTg, SikShowTgSection
   :member-order: bysource


Helper Functions:
------------------

.. autofunction:: batchscanner.parsers.parse_show_tg._gkv

.. autofunction:: batchscanner.parsers.parse_show_tg._vbkild