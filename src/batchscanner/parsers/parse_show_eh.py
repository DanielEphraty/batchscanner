""" A parser for 'show' outputs of EtherHaul and (classic) MultiHaul radios """

from dataclasses import dataclass
import re


@dataclass
class CliResponseParams:
    """ Class for storing parameters of responses to a CLI command
    """
    name: str = ""  # An alias, identifying the response
    regex: str = ""  # The regex to extract the value of interest
    tail_length: int = 0
    format_func: callable = None  # A formatting function for the regex output


class SikShowEh:
    """ Complete doc

    """

    @staticmethod
    def _time_to_days(uptime_str):
        days, hours, minutes, seconds = uptime_str.split(':')
        uptime_in_days = round(float(days) + float(hours) / 24 + float(minutes) / 1440, 2)
        return str(uptime_in_days)

    @staticmethod
    def parse(response: str, params: list[CliResponseParams]) -> dict:
        output = {param.name: '' for param in params}
        for param in params:
            if m := re.search(param.regex, response):
                if param.tail_length:
                    lines = [line.strip() for line in m.groups()[-1].split('\n')]
                    step_back = min(len(lines), param.tail_length)
                    value = '; '.join(lines[-step_back:])
                else:
                    value = [item for item in m.groups() if item][-1]
            else:
                value = None
            if value:
                if param.format_func:
                    value = param.format_func(value)
                output[param.name] = value
        return output

    ### Move to commander
    """
    def _get_free_index(self, show_cmd, identifier, max_index):
        response = self.exec_cmd(show_cmd)
        if response:
            free_index = None
            for index in range(1, max_index + 1):
                x = re.search(fr"{identifier}\s{str(index)}", response)
                if not x:
                    free_index = index
                    break
            return free_index
        else:
            return None
            

    def exec_cmd_with_index(self, set_cmd, show_cmd, identifier, max_index, index_joker='*'):
        index = self._get_free_index(show_cmd, identifier, max_index)
        if index:
            cmd = set_cmd.replace(index_joker, str(index))
            return self.exec_cmd(cmd)
        else:
            self.errors.append(f"Command: '{set_cmd}' failed to execute")
    """

    @staticmethod
    def showbaseunit():
        cmd = "show base-unit"
        params = [CliResponseParams('bu_mac', r'self-mac\s*:\s(\S*)\s'),
                  CliResponseParams('bu_freq', r'frequency\s*:\s(\S*)\s'),
                  CliResponseParams('bu_guest', r'guest-connection\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showeth1():
        cmd = "show eth eth1"
        params = [CliResponseParams('eth1_oper', r'eth1\s+operational\s*:\s(\S*)\s'),
                  CliResponseParams('eth1_speed', r'eth1\s+eth-act-type\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showeth2():
        cmd = "show eth eth2"
        params = [CliResponseParams('eth2_oper', r'eth2\s+operational\s*:\s(\S*)\s'),
                  CliResponseParams('eth2_speed', r'eth2\s+eth-act-type\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showeth3():
        cmd = "show eth eth3"
        params = [CliResponseParams('eth3_oper', r'eth3\s+operational\s*:\s(\S*)\s'),
                  CliResponseParams('eth3_speed', r'eth3\s+eth-act-type\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showeth4():
        cmd = "show eth eth4"
        params = [CliResponseParams('eth4_oper', r'eth4\s+operational\s*:\s(\S*)\s'),
                  CliResponseParams('eth4_speed', r'eth4\s+eth-act-type\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showuseractivitylog(tail_length=1):
        cmd = "show user-activity-log"
        params = [CliResponseParams('events_log', r'(?s)(.*)', tail_length)]
        return cmd, params

    @staticmethod
    def showinventory():
        cmd = "show inventory 1"
        params = [CliResponseParams('inventory_sn', r'inventory 1 serial\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showlldp():
        cmd = "show lldp-remote"
        params = [CliResponseParams('lldp_remote', r'lldp-remote eth0 0 chassis-id\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showlog(tail_length=1):
        cmd = "show log"
        params = [CliResponseParams('events_log', r'(?s)(.*)', tail_length)]
        return cmd, params

    @staticmethod
    def showremoteterminalunit():
        cmd = "show remote-terminal-unit"
        params = []
        for idx in range(1, 9):
            params += [CliResponseParams(f'rtu{idx}_mac', fr'{idx} mac\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_status', fr'{idx} status\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_assoc', fr'{idx} association\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_tx_msc', fr'{idx} tx-mcs\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_rssi', fr'{idx} rssi\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_sig_quality', fr'{idx} signal-quality\s*:\s(\S*)\s'),
                       CliResponseParams(f'rtu{idx}_connect_days', fr'{idx} connect-time\s*:\s(\S*)\s',
                                         0, SikShowEh._time_to_days),
                       ]
        return cmd, params

    @staticmethod
    def showrf():
        cmd = "show rf"
        params = [CliResponseParams('rf_oper', r'rf operational\s*:\s(\S*)\s'),
                  CliResponseParams('rf_cinr', r'rf cinr\s*:\s(\S*)\s'),
                  CliResponseParams('rf_rssi', r'rf rssi\s*:\s(\S*)\s'),
                  CliResponseParams('rf_freq', r'rf (tx-frequency|frequency)\s*:\s(\S*)\s'),
                  CliResponseParams('rf_mode', r'rf mode\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showrfdebug():
        cmd = "show rf-debug"
        params = [CliResponseParams('rfdebug_ptx', r'rf-debug tx-power\s*:\s(\S*)\s'),
                  CliResponseParams('rfdebug_distance', r'rf-debug link-length\s*:\s(\S*)\s'),
                  ]
        return cmd, params

    @staticmethod
    def showsystem():
        cmd = "show system"
        params = [CliResponseParams('system_descrip', r'system description\s*:\s(\S*)\s'),
                  CliResponseParams('system_name', r'system name\s*:\s(\S*)\s'),
                  CliResponseParams('system_location', r'system location\s*:\s(\S*)\s'),
                  CliResponseParams('system_date', r'system date\s*:\s(\S*)\s'),
                  CliResponseParams('system_time', r'system time\s*:\s(\S*)\s'),
                  CliResponseParams('system_up_days', r'system uptime\s*:\s(\S*)\s',
                                    0, SikShowEh._time_to_days),
                  ]
        return cmd, params

    @staticmethod
    def showsw():
        cmd = "show sw"
        active_sw_regex = r'(?m)^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*yes\s+no'
        active_sw_regex += r'|^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*yes\s+yes'
        active_sw_regex += r'|^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*wait-accept\s+no'
        active_sw_regex += r'|^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*wait-accept\s+yes'
        offline_sw_regex = r'(?m)^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*no\s+no'
        offline_sw_regex += r'|^\d\s*\S*?([0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}).*no\s+yes'
        params = [CliResponseParams('sw_active', active_sw_regex),
                  CliResponseParams('sw_offline', offline_sw_regex),
                  ]
        return cmd, params

    @staticmethod
    def showterminalunit():
        cmd = "show terminal-unit"
        params = [CliResponseParams('tu_mac', r'self-mac\s*:\s(\S*)\s'),
                  CliResponseParams('tu_status', r'status\s*:\s(\S*)\s'),
                  CliResponseParams('tu_bu_mac', r'base-unit-mac\s*:\s(\S*)\s'),
                  CliResponseParams('tu_tx_msc', r'tx-mcs\s*:\s(\S*)\s'),
                  CliResponseParams('tu_rssi', r'rssi\s*:\s(\S*)\s'),
                  CliResponseParams('tu_sig_quality', r'signal-quality\s*:\s(\S*)\s'),
                  CliResponseParams('tu_connect_days', r'connect-time\s*:\s(\S*)\s',
                                    0, SikShowEh._time_to_days),
                  ]
        return cmd, params
