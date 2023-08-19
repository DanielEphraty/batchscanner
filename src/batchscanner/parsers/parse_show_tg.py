from collections import abc
import datetime
import ipaddress
import re
from tabulate import tabulate
import typing
import yaml


def _gkv(in_dict: dict) -> tuple[str, typing.Any]:
    """ *gkv* is an acronym for Get Key and Value (from dictionary).

        Return the key and value an item in a dictionary (with a single item).
        If the dictionary has multiple items, the key and value of the first item are returned.
        If the dictionary is empty (or `in_dict` is not a dictionary), returns
        a tuple of empty strings: ('', '').

        :param in_dict: A dictionary with a single element: {key, value}
        :type in_dict: dict
        :return: (key, value) of the first item in `in_dict`
        :rtype: tuple(str, Any)
    """
    key = value = ''
    if type(in_dict) is dict:
        for key, value in in_dict.items():
            break
    return key, value


def _vbkild(list_of_dicts: list[dict], key_id: str, default: typing.Any = None) -> typing.Any:
    """ *vbkild* is an acronym for get Value By Key In List of Dictionaries, where the dictionaries
        are assumed to have a single item.

        Given a list of single-element dictionaries {`key`: `value`}, return `value` of the first
        dictionary where key contains `key_id`.
        If `list_of_dicts` is not a list of dictionaries, or if no dictionary with the right key is found:
        return `default`.

        :param list_of_dicts: A list of single-element dictionaries
        :type list_of_dicts: list[dict]
        :param key_id: A substring for matching the key of each dictionary.
        :type key_id: str
        :param default: value to return if no dictionary with the right key is found.
        :type default: Any
        :return: The value of the skdict {key:value} whose key contains `key_id`
    """
    if type(list_of_dicts) is list:
        for item in list_of_dicts:
            key, value = _gkv(item)
            if key_id in key:
                return value
    return default


class SikShowTg:
    """ A class to parse the output of a TG 'show' dump, and represent the derived parameters (tokens).
    """

    def __init__(self, show_dump, identifier, silent=True):
        """ Parses a `show_dump`: a text dump of a TG 'show' command.

        :param show_dump: a text dump of a TG 'show' command
        :type show_dump: str
        :param identifier: an arbitrary label (typically some unique identifier) used in parsing error messages.
        :type identifier: str
        :param silent: If True, do not print out any errors
        :type silent: bool

        If parsing is successful, attributes (listed below) provide the derived parameters (tokens).
        Each attribute is an instance of :class:`SikShowTgSection`, which is a container for one or more
        identical *atom* classes. Each of these *atom* classes is a subclass of
        :class:`SikShowTgAtom`.

        """
        self.show_dump = show_dump
        self.identifier = identifier
        self.silent = silent
        self.show_parsed = self._deyamlify()
        #: The radio's name (str)
        self.name = self._get_radio_name()
        #: Tokens from the **system** section of 'show'
        self.system = self._tokenise_system()
        #: Tokens from the **interfaces** section of 'show'
        self.interfaces = self._tokenise_interfaces()
        #: Tokens from the **inventory** section of 'show'
        self.inventory = self._tokenise_inventory()
        #: Tokens from the **ip** section of 'show'
        self.ip = self._tokenise_ips()
        #: Tokens from both the **radio-common->node_config** and **radio-common->node_config** sections of 'show'
        self.node = self._tokenise_node()
        self._sectors_common = self._tokenise_sectors_common()
        self._sectors_dn = self._tokenise_sectors_dn()
        #: Tokens from both the **radio-common->sectors_config** and **radio-common->sectors_config'** sections of 'show'
        self.sectors = self._tokenise_sectors()
        self._links_common = self._tokenise_links_common()
        self._links_dn = self._tokenise_links_dn()
        #: Tokens from both the **radio-common->links** and **radio-common->links** sections of 'show'
        self.links = self._tokenise_links()

    def __repr__(self):
        return f"{self.__class__.__name__}: parsed show output for '{self.identifier}'"

    def __str__(self):
        string = ''
        if getattr(self, 'interfaces', None):
            string += str(self.interfaces)
        if getattr(self, 'ip', None):
            string += str(self.ip)
        if getattr(self, 'inventory', None):
            string += str(self.inventory)
        if getattr(self, 'node', None):
            string += str(self.node)
        if getattr(self, 'sectors', None):
            string += str(self.sectors)
        if getattr(self, 'links', None):
            string += str(self.links)
        if getattr(self, 'system', None):
            string += str(self.system)
        return string

    def _deyamlify(self) -> list[dict]:
        """ This function converts the output of a TG 'show' command to standard YAML. It then uses a standard YAML
            library to render the converted output as a list of dictionaries. Each dictionary is single-key, and the key
            equals one of the main sections of the 'show' output: **interfaces**, **inventory**, **system**, ...

            There is no need to explicitly call this function, as it is automatically called
            when instantiating class `:class:SikShowTg`.

            **Conversion to Standard YAML**

            The output of a TG 'show' command is quasi-YAML. The following substitutions are made sequentially,
            in order to convert to standard YAML:

            =============   ==============  ============================================================================
            Change          Into            Comment
            =============   ==============  ============================================================================
            ': '            ':'             Resolves cases where the string ': ' appears as part of a description.
            'key value;'    'key: value'    Simple mapping (key, value)
            'key;'          'key:'          A mapping...
            'name {'        'name:'         Opening of section
            '}'             ''              Closing of section
            =============   ==============  ============================================================================

            Example::

                **Original**                                 **Converted**
                ip {	                                     - ip:
                  ipv4 {	                                - ipv4:
                    address {	                                  - address:
                      ip 172.19.40.10;	                             - ip: 172.19.40.10
                      prefix-length 24;	                             - prefix-length: 24
                      c-vlan 20;	                             - c-vlan: 20
                    }
                    address {	                                  - address:
                      ip 192.168.0.100;	                             - ip: 192.168.0.100
                      prefix-length 24;	                             - prefix-length: 24
                    }
                    default-gateway 172.19.40.1;	          - default-gateway: 172.19.40.1
                  }
                  ipv6 {	                                - ipv6:
                    link-local fe80::6:7bff:fe2d:3790;	          - link-local: fe80::6:7bff:fe2d:3790
                   }
                }

            **Parsing the Standard YAML**

            The converted output (standard YAML) is parsed using the
            `PyYAML <https://pypi.org/project/PyYAML/>`_, library into Python lists and dictionaries.
            This typically comprises a list of dictionaries, where each dictionary has a *single* element.
            For instance, the `ipv4` subsection (in the example above) is parsed into::

                [{'address': [{'ip': '172.19.40.10'}, {'prefix-length': 24}, {'c-vlan': 20}]},
                 {'address': [{'ip': '192.168.0.100'}, {'prefix-length': 24}]},
                 {'default-gateway': '172.19.40.1'}
                ]

            In addition, within a list, *the keys of the dictionaries are not necessarily unique*.
            In the example above, two dictionaries in the list have the same key: `address`.
            Duplicate keys are prevalent in earlier TG (embedded) software versions (up to and including 2.0.0).
            As of software version 2.1.1 (with the addition of SNMP support), most keys are unique. Here's the
            equivalent of the above example in version 2.1.1::

                [{'address 172.19.40.10': [{'prefix-length': 24}, {'c-vlan': 20}]},
                 {'address 192.168.0.100': [{'prefix-length': 24}]},
                 {'default-gateway': '172.19.40.1'}
                ]

            In order to effectively parse the above type of lists of dictionaries, two helper functions
            are heavily used throughout the code: :func:`_gkv` and :func:`_vbkild`.
        """

        # Convert tg 'show' output to standard YAML
        lines = self.show_dump.split('\n')
        lines_out = []
        for line in lines:
            # Fix cases where ': ' appears as part of a description
            line = re.sub(r': ', ':', line)
            # A line with mapping (key, value):         key value; -> - key: value
            line_out = re.sub(r'(\s*)(\S+)\s(.+);', r'\1- \2: \3', line)
            if line == line_out:
                # A line with mapping (key, no value):  key;       -> key:
                line_out = re.sub(r'(\s*)(\S+);', r'\1- \2: ', line)
            if line == line_out:
                # A line opening a section:             name {      -> - name:
                line_out = re.sub(r'(\s*)(.+)\s{', r'\1- \2: ', line)
            if line == line_out:
                # A line closing a section:             }             -> discard
                line_out = re.sub(r'.*}', '', line_out)
            lines_out.append(line_out)
        # Parse as YAML
        try:
            parsed = yaml.safe_load('\n'.join(lines_out))
        except yaml.YAMLError as e:
            if not self.silent:
                print(f"Error trying to YAML-parse for {self.identifier}: {e}")
            return []
        else:
            return parsed

    def _get_radio_name(self):
        """ Get the radio *name* by tokenising the relvant part of the **system** section of the TG show dump.
        """
        system = _vbkild(self.show_parsed, 'system')
        return _vbkild(system, 'name', 'unknown')

    def _tokenise_interfaces(self):
        """ Tokenise the **interfaces** section of the TG show dump.
        """
        token = 'interfaces'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        interfaces = _vbkild(self.show_parsed, token)
        try:
            interfaces.pop(0)  # Discard information about interface 'host'
            for interface in interfaces:
                container.append(SikShowTgAtomInterface(interface))
        except Exception as e:
            if not self.silent:
                print(f"Error trying to tokenise '{token}' for {self.identifier}: {e}")
        return container

    def _tokenise_inventory(self):
        """ Tokenise the **inventory** section of the TG show dump.
        """
        token = 'inventory'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        inventory_items = _vbkild(self.show_parsed, token)
        # Find record corresponding to the radio itself (does not have a 'parent' attribute)
        if inventory_items:
            for inventory_item in inventory_items:
                _, details = _gkv(inventory_item)
                if not _vbkild(details, 'parent'):
                    try:
                        container.append((SikShowTgAtomInventory(details)))
                    except Exception as e:
                        if not self.silent:
                            print(f"Error trying to tokenise '{token}' for {self.identifier}: {e}")
        return container

    def _tokenise_ips(self):
        """ Tokenise the **ip** section of the TG show dump.
        """
        token = 'ip'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        ip = _vbkild(self.show_parsed, token)
        ipv4 = _vbkild(ip, 'ipv4')
        gateway = None
        try:
            for ip_item in ipv4:
                ip_title, ip_details = _gkv(ip_item)
                if ip_title == 'default-gateway':
                    gateway = ip_details
                else:
                    container.append(SikShowTgAtomIp(ip_item))
            # Pair one of the IP addresses with the default gateway
            if gateway:
                gateway_ip = ipaddress.IPv4Address(gateway)
                for atomip in container:
                    network = ipaddress.IPv4Network(f"{atomip.address}/{atomip.pref}", strict=False)
                    if gateway_ip in network:
                        atomip.gateway = gateway_ip
                        break
        except Exception as e:
            if not self.silent:
                print(f"Error trying to tokenise '{token}' for {self.identifier}: {e}")
        return container

    def _tokenise_node(self):
        """ Tokenise the **radio-common->node-config** and **radio-dn->node-config** sections of the TG show dump.
        """
        token = 'node'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        common = _vbkild(_vbkild(self.show_parsed, 'radio-common'), 'node-config')
        dn = _vbkild(_vbkild(self.show_parsed, 'radio-dn'), 'node-config')
        try:
            container.append(SikShowTgAtomNode(common, dn))
        except Exception as e:
            if not self.silent:
                print(f"Error trying to tokenise Node for {self.identifier}: {e}")
        return container

    def _tokenise_sectors(self):
        """ Combine information from:
              - **radio-common->sectors-config** section of the TG show dump (as tokenised in `_sectors_common`)
              - **radio-dn->sectors-config** section of the TG show dump (as tokenised in _sectors_dn).
        """
        sectors_common = self._sectors_common
        sectors_dn = self._sectors_dn
        container = SikShowTgSection(self.identifier, self.name, 'Sectors')
        # Try to pair up the tokens from sectors_common and sectors_dn. First loop over one, then the other
        indeces = []
        for common in sectors_common:
            indeces.append(common.index)
            for dn in sectors_dn:
                if dn.index == common.index:
                    container.append(SikShowTgAtomSector(common, dn))
                    break
            else:
                container.append(SikShowTgAtomSector(common, None))
        for dn in sectors_dn:
            if dn.index not in indeces:
                container.append(SikShowTgAtomSector(None, dn))
        return container

    def _tokenise_sectors_common(self):
        """ Tokenise the **radio-common->sectors-config** section of the TG show dump.
        """
        token = 'sectors_common'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        common = _vbkild(_vbkild(self.show_parsed, 'radio-common'), 'sectors-config')
        if common:
            for sector in common:
                container.append(SikShowTgAtomSectorCommon(sector))
        return container

    def _tokenise_sectors_dn(self):
        """ Tokenise the **radio-dn->sectors-config** section of the TG show dump.
        """
        token = 'sectors_dn'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        dn = _vbkild(_vbkild(self.show_parsed, 'radio-dn'), 'sectors-config')
        if dn:
            for sector in dn:
                container.append(SikShowTgAtomSectorDn(sector, self.node[0]))
        return container

    def _tokenise_links(self):
        """ Combine information from:
              - **radio-common->links** section of the TG show dump (as tokenised in `_links_common`)
              - **radio-dn->links** section of the TG show dump (as tokenised in _links_dn).
        """
        links_common = self._links_common
        links_dn = self._links_dn
        container = SikShowTgSection(self.identifier, self.name, 'Links')
        # Try to pair up the tokens from links_common and links_dn. First loop over one, then the other
        remotes = []
        for common in links_common:
            remotes.append(common.remote)
            for dn in links_dn:
                if dn.remote == common.remote:
                    container.append(SikShowTgAtomLink(common, dn))
                    break
            else:
                container.append(SikShowTgAtomLink(common, None))
        for dn in links_dn:
            if dn.remote not in remotes:
                container.append(SikShowTgAtomLink(None, dn))
                container[-1].status = 'disconnected'
        return container

    def _tokenise_links_common(self):
        """ Tokenise the **radio-common->links** section of the TG show dump.
        """
        token = 'links_common'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        common = _vbkild(_vbkild(self.show_parsed, 'radio-common'), 'links')
        if common:
            for link in common:
                container.append(SikShowTgAtomLinkCommon(link))
        return container

    def _tokenise_links_dn(self):
        """ Tokenise the **radio-dn->links** section of the TG show dump.
        """
        token = 'links_dn'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        dn = _vbkild(_vbkild(self.show_parsed, 'radio-dn'), 'links')
        if dn:
            for link in dn:
                container.append(SikShowTgAtomLinkDn(link))
        return container

    def _tokenise_system(self):
        """ Tokenise the **system** section of the TG show dump.
        """
        token = 'system'
        container = SikShowTgSection(self.identifier, self.name, token.capitalize())
        system = _vbkild(self.show_parsed, token)
        try:
            container.append(SikShowTgAtomSystem(system))
        except Exception as e:
            if not self.silent:
                print(f"Error trying to tokenise '{token}' for {self.identifier}: {e}")
        return container


class SikShowTgSection(abc.MutableSequence):
    """ A Container for *atoms*: the subclasses of :class:`TgAtoms`.
        This container is implemented as a
        `abc.MutableSequence <https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableSequence>`_.
        Essentially a list with some added functionality.
    """

    def __init__(self, identifier:str, name: str, section: str = ''):
        """ Initialises an instance of the class.

            :param name: an arbitrary identifier, typically the name of the radio
            :type name: str
            :param section: an arbitrary identifier, typically the name of the section within the 'show' dump
            :type section: str
        """
        self.identifier = identifier
        self.name = name
        self.section = section
        self.container = []

    def __delitem__(self, position):
        del self.container[position]

    def __getitem__(self, item):
        return self.container[item]

    def __len__(self):
        return len(self.container)

    def __setitem__(self, position, value):
        self.container[position] = value

    def __repr__(self):
        string = f"{self.__class__.__name__}( name={self.name}\n\t"
        if self.container:
            string += '\n\t'.join([repr(atom) for atom in self.container])
            string += '\n\t)'
            return string
        else:
            return 'Empty Container'

    def __str__(self):
        if self.container:
            string = f"\n{self.section}:\n"
            prefix = {'name': self.name}
            data = [prefix | atom.todict() for atom in self.container]
            return string + tabulate(data, headers='keys', tablefmt='plain', numalign='left') + '\n'

        else:
            return 'Empty Section'

    def insert(self, position, value):
        """
        :meta private:
        """
        self.container.insert(position, value)

    def tocsv(self) -> (str, str):
        """ Dumps container (instance of :class:`SikShowTgSection`) as csv

            :return: Returns a tuple of 2 strings:

                      1. Comma-separated field names
                      2. Lines of comma-separated values, where each line corresponds to one atom in the container, and
                         lines are separated with a newline character.
            :rtype: tuple(str, str)
        """
        if self.container:
            # Tokens
            tokens = ['date', 'route', 'name']
            tokens.extend(self.container[0].todict().keys())
            tokens_csv = ','.join(tokens) + '\n'
            # Values
            timestamp = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            data_csv = ''
            for atom in self.container:
                data = f"{timestamp},{self.identifier},{self.name},{atom.tocsv()}\n"
                data_csv += data
            return tokens_csv, data_csv
        else:
            return '', ''


class SikShowTgAtom:
    """ A base class for *atoms*: classes representing tokens extracted from the TG 'show' dump.
        """

    #: A dictionary mapping names of attributes (as used in code) to labels (as shown to user).
    #: Assigned in each subclass.
    tokens = {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.todict()})"

    def __str__(self):
        return tabulate(self.todict(), headers='keys', tablefmt='plain', numalign='left')

    def _init_tokens(self):
        for key, _ in self.tokens.items():
            setattr(self, key, '')

    def tocsv(self):
        """ Docstring here
        """
        return ','.join([f"{getattr(self, key)}" for key in self.tokens.keys()])

    def todict(self):
        """ Docstring here
        """
        return {value: getattr(self, key) for key, value in self.tokens.items()}

    @staticmethod
    def _helper_cannonise_sw_ver(sw_ver: str, shortest: bool = False):
        """ Remove last part of sw version string"""
        if sw_ver:
            if m := re.match(r'(\d+)\.(\d+)\.(\d+)\D+(\d+)', sw_ver):
                m_tuple = m.groups()
                short = '.'.join(m_tuple[0:-1])
                if shortest:
                    return short
                else:
                    return f"{short}-{m_tuple[-1]}"
            else:
                return 'unknown'
        else:
            return 'unavail'


class SikShowTgAtomSystem(SikShowTgAtom):
    """ Tokens derived from the **system** section of the 'show' dump.
    """
    def __init__(self, system):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'product': 'product',
                       'uptime': 'uptime',
                       'datetime': 'datetime',
                       'location': 'location',
                       'sw_active': 'sw_active',
                       'sw_passive': 'sw_passive',
                       'gps_mode': 'gps_mode',
                       'gps_sats': 'gps_sats',
                       }
        self._init_tokens()
        self.parse(system)

    def parse(self, system):
        location = _vbkild(system, 'location', self.location)
        self.location = str(location).replace(',',';')
        state = _vbkild(system, 'state')
        self.product = _vbkild(state, 'product', self.product)
        uptime = _vbkild(state, 'uptime', self.uptime)
        self.uptime = uptime
        uptime_parts = str(uptime).split(':')
        if len(uptime_parts) == 4 and len(uptime_parts[0]) == 4:
            self.uptime = f"0{str(uptime)}"
        self.datetime = _vbkild(state, 'date-and-time', self.datetime)
        gps = _vbkild(state, 'gps')
        self.gps_mode = _vbkild(gps, 'fix-mode', self.gps_mode)
        self.gps_sats = _vbkild(gps, 'fix-satellites-number', self.gps_sats)
        banks = _vbkild(state, 'banks-info')
        for bank in banks:
            _, bank_info = _gkv(bank)
            version = self._helper_cannonise_sw_ver(_vbkild(bank_info, 'software-version'), shortest=True)
            match _vbkild(bank_info, 'status'):
                case 'active':
                    self.sw_active = version
                case 'passive':
                    self.sw_passive = version


class SikShowTgAtomInterface(SikShowTgAtom):
    """ Tokens derived from the **interfaces** section of the 'show' dump.
    """

    def __init__(self, interface):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'port': 'port',
                       'status': 'status',
                       'duplex': 'dup',
                       'speed': 'speed',
                       }
        self._init_tokens()
        self.parse(interface)

    def parse(self, data):
        # Port names may be either in dictionary key, or within dictionary under sub-key 'name'
        port_title, port_data = _gkv(data)
        port = _vbkild(port_data, 'name', 'unknown')
        if port == 'unknown':
            if m := re.match(r'ports (.+)', port_title):
                port = m[1]
            elif m := re.match(r'rf-interface (.+)', port_title):
                port = m[1]
        self.port = port
        admin_status = _vbkild(port_data, 'admin-status', '')
        state = _vbkild(port_data, 'state')
        oper_status = _vbkild(state, 'oper-status', '')
        duplex = _vbkild(state, 'actual-duplex-mode', self.duplex)
        match duplex:
            case 'full':
                self.duplex = 'FD'
            case 'half':
                self.duplex = 'HD'
            case _:
                self.duplex = duplex
        self.speed = _vbkild(state, 'actual-port-speed', self.speed)
        if admin_status == 'down':
            self.status = 'user-disabled'
        elif oper_status:
            self.status = oper_status
        else:
            self.status = ''


class SikShowTgAtomInventory(SikShowTgAtom):
    """ Tokens derived from the **inventory** section of the 'show' dump.
    """
    def __init__(self, interface):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'sn': 'sn',
                       'model': 'model',
                       'hw_rev': 'hw_rev',
                       'sw_ver': 'sw_ver',
                       }
        self._init_tokens()
        self.parse(interface)

    def parse(self, interface):
        self.sn = _vbkild(interface, 'serial-num', self.sn)
        self.model = _vbkild(interface, 'model-name', self.model)
        self.hw_rev = _vbkild(interface, 'hardware-rev', self.hw_rev)
        self.sw_ver = self._helper_cannonise_sw_ver(_vbkild(interface, 'software-rev', self.sw_ver))


class SikShowTgAtomIp(SikShowTgAtom):
    """ Tokens derived from the **ip** section of the 'show' dump.
    """

    def __init__(self, ip_data):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'address': 'address',
                       'pref': 'pref',
                       'vlan': 'vlan',
                       'gateway': 'gateway',
                       }
        self._init_tokens()
        self.parse(ip_data)

    def parse(self, ip_data):
        ip_title, ip_details = _gkv(ip_data)
        address = _vbkild(ip_details, 'ip')
        if not address:
            if m := re.match(r'address (.+)', ip_title):
                address = m[1]
        self.address = ipaddress.IPv4Address(address)
        self.pref = _vbkild(ip_details, 'prefix-length', self.pref)
        cvlan = _vbkild(ip_details, 'c-vlan')
        if cvlan:
            self.vlan = f"c{cvlan}"


class SikShowTgAtomNode(SikShowTgAtom):
    """ Tokens derived from the **radio-common->node-config** and **radio-dn->node-config**
        sections of the 'show' dump.
    """

    def __init__(self, common, dn):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'popdn': 'popdn',
                       'sync': 'sync',
                       'mode': 'mode',
                       'sched': 'sched',
                       'ptx': 'ptx',
                       'freq': 'freq',
                       'polarity': 'pol',
                       'golay': 'gol',
                       }
        self._init_tokens()
        self.parse(common, dn)

    def parse(self, common, dn):
        self.mode = _vbkild(common, 'operation-mode', self.mode)
        self.sched = _vbkild(common, 'link-distance', self.sched)
        self.ptx = _vbkild(common, 'tx-power-control', self.ptx)
        self.popdn = _vbkild(dn, 'is-pop-dn', self.popdn)
        self.sync = _vbkild(dn, 'sync-mode', self.sync)
        profile = _vbkild(dn, 'default-radio-profile')
        self.freq = _vbkild(profile, 'frequency', self.freq)
        if self.freq == 'unspecified':
            self.freq == 'unspec'
        self.polarity = _vbkild(profile, 'polarity', self.polarity)
        if self.polarity == 'unspecified':
            self.polarity = 'unspec'
        tx_golay = _vbkild(profile, 'tx-golay-index', '')
        if tx_golay == 'unspecified':
            tx_golay = 'unspec'
        rx_golay = _vbkild(profile, 'rx-golay-index', '')
        if rx_golay == 'unspecified':
            rx_golay = 'unspec'
        self.golay = f"{tx_golay}|{rx_golay}"


class SikShowTgAtomSectorCommon(SikShowTgAtom):
    """ Tokens derived from the **radio-common->sector-config** section of the 'show' dump.
    """

    def __init__(self, common):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'index': 'sec',
                       'admin': 'admin',
                       'freq_actual': 'act_f',
                       'antenna': 'ant',
                       'sync': 'sync',
                       'temp_modem': 'Tmdm',
                       'temp_rf': 'Trf',
                       }
        self._init_tokens()
        self.parse(common)

    def parse(self, common):
        # Parse sector information from radio-common
        sector_title, sector_details = _gkv(common)
        index = _vbkild(sector_details, 'index')
        if not index:
            if m := re.match(r'sector (.+)', sector_title):
                index = m[1]
        self.index = index
        self.admin = _vbkild(sector_details, 'admin-status', self.admin)
        if self.admin != 'down':
            state = _vbkild(sector_details, 'state')
            self.freq_actual = _vbkild(state, 'frequency', self.freq_actual)
            self.antenna = _vbkild(state, 'antenna-mode', self.antenna)
            self.sync = _vbkild(state, 'sync-mode', self.sync)
            temps = _vbkild(state, 'temperatures')
            self.temp_modem = _vbkild(temps, 'modem-temperature')
            rf = _vbkild(temps, 'rf')
            self.temp_rf = _vbkild(rf, 'rf-temperature')


class SikShowTgAtomSectorDn(SikShowTgAtom):
    """ Tokens derived from the **radio-dn->sector-config** section of the 'show' dump.
    """

    def __init__(self, dn, node):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'index': 'sec',
                       'freq_config': 'cfg_f',
                       'polarity': 'pol',
                       'golay': 'gol', }
        self._init_tokens()
        self.parse(dn, node)

    def parse(self, dn, node):
        # Parse sector information from radio-dn
        sector_title, sector_details = _gkv(dn)
        index = _vbkild(sector_details, 'index')
        if not index:
            if m := re.match(r'sector (.+)', sector_title):
                index = m[1]
        self.index = index
        radio_profile = _vbkild(sector_details, 'radio-profile')
        self.freq_config = _vbkild(radio_profile, 'frequency', self.freq_config)
        if str(self.freq_config).lower() == 'unspecified':
            self.freq_config = node.freq
        self.polarity = _vbkild(radio_profile, 'polarity', self.polarity)
        if self.polarity.lower() == 'unspecified':
            self.polarity = node.polarity
        tx_golay = _vbkild(radio_profile, 'tx-golay-index', '')
        rx_golay = _vbkild(radio_profile, 'rx-golay-index', '')
        if tx_golay == 'unspecified' and rx_golay == 'unspecified':
            self.golay = node.golay
        else:
            self.golay = f"{tx_golay}|{rx_golay}"


class SikShowTgAtomSector(SikShowTgAtom):
    """ Tokens derived by merging tokens from :class:`SikShowTgAtomSectorDn` and :class:`SikShowTgAtomSectorCommon`.
    """

    def __init__(self, common, dn):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'index': 'sec',
                       'admin': 'admin',
                       'freq_config': 'cfg_f',
                       'polarity': 'pol',
                       'golay': 'gol',
                       'freq_actual': 'act_f',
                       'antenna': 'ant',
                       'sync': 'sync',
                       'temp_modem': 'Tmdm',
                       'temp_rf': 'Trf',
                       }
        self._init_tokens()
        # Merge tokens from SikShowTgAtomSectorCommon and SikShowTgAtomSectorDn
        for token in self.tokens.keys():
            try:
                value = getattr(common, token)
            except AttributeError:
                try:
                    value = getattr(dn, token)
                except AttributeError:
                    value = ''
            setattr(self, token, value)
        # Flag contradiction between configured frequency and actual frequency
        if self.freq_actual and self.freq_config:
            if self.freq_actual == self.freq_config:
                self.freq_actual = str(self.freq_actual) + ' (ok)'
            else:
                self.freq_actual = str(self.freq_actual) + ' (KO!)'


class SikShowTgAtomLinkCommon(SikShowTgAtom):
    """ Tokens derived from the **radio-common->links** section of the 'show' dump.
    """

    def __init__(self, common):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'remote': 'remote',
                       'status': 'status',
                       'uptime': 'uptime',
                       'role': 'role',
                       'act_sector_local': 'act_lsec',
                       'act_sector_remote': 'act_rsec',
                       'rssi': 'rssi',
                       'snr': 'snr',
                       'mcs_tx': 'mcs_tx',
                       'mcs_rx': 'mcs_rx',
                       'tiles_tx': 'tiles_tx',
                       'tiles_rx': 'tiles_rx',
                       'per_tx': 'per_tx',
                       'per_rx': 'per_rx',
                       'beam_index_tx': 'beam_index_tx',
                       'beam_index_rx': 'beam_index_rx',
                       }
        self._init_tokens()
        self.parse(common)

    def parse(self, common):
        # Parse sector information from radio-common
        link_title, link_details = _gkv(common)
        if link_title == 'active':
            self.status = 'active'
            self.remote = _vbkild(link_details, 'remote-assigned-name', self.remote)
        elif link_title == 'disconnected':
            self.status = 'disconnected'
            self.remote = _vbkild(link_details, 'remote-assigned-name', self.remote)
        elif m := re.match(r'active (.+)', link_title):
            self.status = 'active'
            self.remote = m[1]
        elif m := re.match(r'disconnected (.+)', link_title):
            self.status = 'disconnected'
            self.remote = m[1]
        if self.status == 'active':
            uptime = _vbkild(link_details, 'link-uptime')
            if type(uptime) is str:
                self.uptime = uptime
            else:
                self.uptime = self._uptime_to_str(uptime)
            role = _vbkild(link_details, 'local-role', self.role)
            self.role = role[0:min(4, len(role))]
            self.act_sector_local = _vbkild(link_details, 'actual-local-sector-index', self.act_sector_local)
            self.act_sector_remote = _vbkild(link_details, 'actual-remote-sector-index', self.remote)
            self.rssi = _vbkild(link_details, 'rssi', '')
            self.snr = _vbkild(link_details, 'snr', '')
            self.mcs_tx = _vbkild(link_details, 'mcs-tx', '')
            self.mcs_rx = _vbkild(link_details, 'mcs-rx', '')
            self.tiles_tx = _vbkild(link_details, 'active-tile-count-tx', '')
            self.tiles_rx = _vbkild(link_details, 'active-tile-count-rx', '')
            self.per_tx = _vbkild(link_details, 'tx-per', '')
            self.per_rx = _vbkild(link_details, 'rx-per', '')
            self.beam_index_tx = _vbkild(link_details, 'beam-index-tx', '')
            self.beam_index_rx = _vbkild(link_details, 'beam-index-rx', '')

    @staticmethod
    def _uptime_to_str(uptime):
        try:
            string = str(datetime.timedelta(seconds=uptime))
        except TypeError:
            return 'error parsing'
        if m := re.match(r'(\d+) day.*(\d+):(\d+):(\d+)', string):
            d, h, m, s = (m[1], m[2], m[3], m[4])
        elif m := re.match(r'(\d+):(\d+):(\d+)', string):
            d, h, m, s = (0, m[1], m[2], m[3])
        else:
            return str(uptime)
        return f"{int(d):05}:{int(h):02}:{int(m):02}:{int(s):02}"


class SikShowTgAtomLinkDn(SikShowTgAtom):
    """ Tokens derived from the **radio-dn->sector-config** section of the 'show' dump.
    """

    def __init__(self, dn):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'remote': 'remote',
                       'admin': 'admin',
                       'link_type': 'type',
                       'cfg_sector_local': 'cfg_lsec',
                       'cfg_sector_remote': 'cfg_rsec',
                       }
        self._init_tokens()
        self.parse(dn)

    def parse(self, dn):
        # Parse sector information from radio-dn
        link_title, link_details = _gkv(dn)
        if link_title == 'configured':
            self.remote = _vbkild(link_details, 'remote-assigned-name')
        elif m := re.match(r'configured (.+)', link_title):
            self.remote = m[1]
        else:
            return
        self.admin = _vbkild(link_details, 'admin-status', self.admin)
        link_type = _vbkild(link_details, 'responder-node-type', '')
        super_frame = _vbkild(link_details, 'control-superframe', '')
        match link_type:
            case 'cn':
                self.link_type = 'cn'
            case 'dn':
                self.link_type = f"dn{super_frame}"
        local_sectors = ''
        remote_sectors = ''
        if type(link_details) is list:
            for item in link_details:
                item_title, item_detail = _gkv(item)
                if 'local-sector' in item_title:
                    sector = _vbkild(item_detail, 'index')
                    if not sector:
                        if m := re.match(r'local-sector (.+)', item_title):
                            sector = m[1]
                    local_sectors += str(sector)
                elif 'remote-sector' in item_title:
                    sector = _vbkild(item_detail, 'index')
                    if not sector:
                        if m := re.match(r'remote-sector (.+)', item_title):
                            sector = m[1]
                    remote_sectors += str(sector)
        self.cfg_sector_local = local_sectors
        self.cfg_sector_remote = remote_sectors


class SikShowTgAtomLink(SikShowTgAtom):
    """ Tokens derived by merging tokens from :class:`SikShowTgAtomLinkDn` and :class:`SikShowTgAtomLinkCommon`.
    """

    def __init__(self, common, dn):
        #: If required, change only the dictionary values in `tokens` (changing the keys will break the code)
        self.tokens = {'remote': 'remote',
                       'admin': 'admin',
                       'role': 'role',
                       'status': 'status',
                       'uptime': 'uptime',
                       'link_type': 'type',
                       'cfg_sector_local': 'cfg_lsec',
                       'cfg_sector_remote': 'cfg_rsec',
                       'act_sector_local': 'act_lsec',
                       'act_sector_remote': 'act_rsec',
                       'rssi': 'rssi',
                       'snr': 'snr',
                       'mcs_tx': 'mcs_tx',
                       'mcs_rx': 'mcs_rx',
                       'tiles_tx': 'tiles_tx',
                       'tiles_rx': 'tiles_rx',
                       'per_tx': 'per_tx',
                       'per_rx': 'per_rx',
                       'beam_index_tx': 'beam_index_tx',
                       'beam_index_rx': 'beam_index_rx',
                       }
        self._init_tokens()
        # Merge tokens from SikShowTgAtomLinkCommon and SikShowTgAtomLinkDn
        for token in self.tokens.keys():
            try:
                value = getattr(common, token)
            except AttributeError:
                try:
                    value = getattr(dn, token)
                except AttributeError:
                    value = ''
            setattr(self, token, value)
