#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jedelman8@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

DOCUMENTATION = '''
---

module: nxos_get_interface
short_description: Gets details stats or basic info on a particular interface
description:
    - Gets details stats on a particular interface
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - Equivalent to using 'show interface $INTERFACEX/Y' or 'show ip interface $INTERFACEX/Y' 
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    interface:
        description:
            - Name of interface, i.e. Ethernet1/1
        required: true
        default: false
        choices: []
        aliases: []
    detail:
        description:
            - If True, returns detailed stats
        required: false
        default: null
        choices: [true, false]
        aliases: []
    host:
        description:
            - IP Address or hostname (resolvable by Ansible control host)
              of the target NX-API enabled switch
        required: true
        default: null
        choices: []
        aliases: []
    username:
        description:
            - Username used to login to the switch
        required: false
        default: null
        choices: []
        aliases: []
    password:
        description:
            - Password used to login to the switch
        required: false
        default: null
        choices: []
        aliases: []
    protocol:
        description:
            - Dictates connection protocol to use for NX-API
        required: false
        default: http
        choices: ['http', 'https']
        aliases: []
'''

EXAMPLES = '''
# retrieve details info and stats on an interface (from 'show interface')
- nxos_get_interface: interface=Ethernet1/1 host={{ inventory_hostname }} detail=true

# retrieve details info on an interface (from 'show ip interface')
- nxos_get_interface: interface=Ethernet1/1 host={{ inventory_hostname }}

'''

RETURN = '''
interface:
    description:
        - Show multiple information about the interface.
    returned: always
    type: dict
    sample: {"interface":"eth2/1","ip_addr": "10.10.50.1",
            "mask": "24","subnet": "10.10.50.0","type": "ethernet",
            "vrf": "test"}
'''

import socket
import xmltodict
try:
    HAS_PYCSCO = True
    from pycsco.nxos.device import Device
    from pycsco.nxos.device import Auth
    from pycsco.nxos.error import CLIError
except ImportError as ie:
    HAS_PYCSCO = False


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def parsed_data_from_device(device, command, module):

    try:
        data = device.show(command)
    except CLIError as clie:
        module.fail_json(msg='Error sending {}'.format(command),
                         error=str(clie))

    data_dict = xmltodict.parse(data[1])
    body = data_dict['ins_api']['outputs']['output']['body']

    return body


def get_interface_type(interface):
    """Gets the type of interface
    Args:
        interface (str): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20
    Returns:
        type of interface: ethernet, svi, loopback, management, portchannel,
         or unknown
    """
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def get_manual_interface_attributes(device, interface):
    """Gets admin state and description of a SVI interface
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of SVI interface, i.e. vlan10
    Returns:
        dictionary that has two k/v pairs: admin_state & description
            if not an svi, returns None
    """

    if get_interface_type(interface) == 'svi':
        command = 'show interface ' + interface
        try:
            get_data = device.show(command, text=True)
            data_dict = xmltodict.parse(get_data[1])
            show_command = data_dict['ins_api']['outputs']['output']['body']
        except (KeyError, CLIError):
            return None

        if show_command:
            command_list = show_command.split('\n')
            desc = None
            admin_state = 'up'
            for each in command_list:
                if 'Description:' in each:
                    line = each.split('Description:')
                    desc = line[1].strip().split('MTU')[0].strip()
                elif 'Administratively down' in each:
                    admin_state = 'down'

            return dict(description=desc, admin_state=admin_state)
    else:
        return None


def get_interface(device, intf, module):
    """Gets current config/state of interface
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        intf (string): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20
    Returns:
      dictionary that has relevant config/state data about the given
          interface based on the type of interface it is
    """
    base_key_map = {
        'interface': 'interface',
        'admin_state': 'admin_state',
        'desc': 'description',
    }
    speed_map = {
        'eth_duplex': 'duplex',
        'eth_speed': 'speed',
    }
    mode_map = {
        'eth_mode': 'mode'
    }
    loop_map = {
        'state': 'admin_state'
    }
    svi_map = {
        'svi_admin_state': 'admin_state',
        'desc': 'description'
    }
    mode_value_map = {
        "mode": {
            "access": "layer2",
            "trunk": "layer2",
            "routed": "layer3",
            "layer3": "layer3"
        }
    }

    key_map = {}
    interface = {}

    command = 'show interface ' + intf

    body = parsed_data_from_device(device, command, module)

    if body:
        interface_table = body['TABLE_interface']['ROW_interface']

        intf_type = get_interface_type(intf)
        if intf_type in ['portchannel', 'ethernet']:
            if not interface_table.get('eth_mode'):
                interface_table['eth_mode'] = 'layer3'

        if intf_type == 'ethernet':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            interface.update(temp_dict)

        elif intf_type == 'svi':
            key_map.update(svi_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)
            attributes = get_manual_interface_attributes(device, intf)
            interface['admin_state'] = str(attributes.get('admin_state',
                                                          'nxapibug'))
            interface['description'] = str(attributes.get('description',
                                                          'nxapi_bug'))
        elif intf_type == 'loopback':
            key_map.update(base_key_map)
            key_map.pop('admin_state')
            key_map.update(loop_map)
            temp_dict = apply_key_map(key_map, interface_table)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

        elif intf_type == 'management':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)

        elif intf_type == 'portchannel':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

        if intf_type in ['ethernet', 'portchannel']:
            mode = interface.get('mode')
        elif (intf_type == 'loopback' or intf_type == 'svi' or
                intf_type == 'management'):
            mode = 'layer3'

    interface['type'] = intf_type

    if interface_table.get('eth_speed'):
        interface['speed'] = get_interface_speed(
            interface_table.get('eth_speed'))

    return interface, mode, interface_table


def get_interface_speed(speed):
    """Translates speed into bits/sec given the output from the API
    Args:
        speed (string): input should be from NX-API in the form of '10 Gb/s'-
            param being sent should be "eth_speed" from output from
            'show interface eth x/y' in NX-API
    Returns:
        equivalent speed (str) in bits per second or "auto"
    """
    if speed.startswith('auto'):
        return 'auto'
    elif speed.startswith('40'):
        return '40000'
    elif speed.startswith('100 G'):
        return '100000'
    elif speed.startswith('10'):
        return '10000'
    elif speed.startswith('1'):
        return '1000'
    elif speed.startswith('100 M'):
        return '100'


def get_interfaces_dict(device, module):
    """Gets all active interfaces on a given switch
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
    Returns:
        dictionary with interface type (ethernet,svi,loop,portchannel) as the
            keys.  Each value is a list of interfaces of given interface (key)
            type.
    """
    command = 'show interface status'
    interfaces_body = parsed_data_from_device(device, command, module)
    interfaces = {
        'ethernet': [],
        'svi': [],
        'loopback': [],
        'management': [],
        'portchannel': [],
        'unknown': []
        }

    interface_list = interfaces_body['TABLE_interface']['ROW_interface']
    for interface in interface_list:
        intf = interface['interface']
        intf_type = get_interface_type(intf)

        interfaces[intf_type].append(intf)

    return interfaces


def normalize_interface(if_name):
    """Return the normalized interface name
    """
    def _get_number(if_name):
        digits = ''
        for char in if_name:
            if char.isdigit() or char == '/':
                digits += char
        return digits

    if if_name.lower().startswith('et'):
        if_type = 'Ethernet'
    elif if_name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif if_name.lower().startswith('lo'):
        if_type = 'loopback'
    elif if_name.lower().startswith('po'):
        if_type = 'port-channel'
    else:
        if_type = None

    number_list = if_name.split(' ')
    if len(number_list) == 2:
        number = number_list[-1].strip()
    else:
        number = _get_number(if_name)

    if if_type:
        proper_interface = if_type + number
    else:
        proper_interface = if_name

    return proper_interface


def get_interface_detailed_info(detailed_interface_table, interface, module):
    detailed_interface = {}

    key_map = {
                "state": "state",
                "eth_members": "members",
                "admin_state": "admin_state",
                "share_state": "share_state",
                "eth_hw_desc": "hw_desc",
                "eth_hw_addr": "hw_addr",
                "eth_bia_addr": "bia_addr",
                "description": "description",
                "eth_mtu": "mtu",
                "desc": "description",
                "eth_bw": "bw",
                "eth_dly": "delay",
                "eth_reliability": "reliability",
                "eth_txload": "tx_load",
                "eth_rxload": "rx_load",
                "medium": "medium",
                "eth_mode": "mode",
                "eth_beacon": "beacon",
                "eth_duplex": "duplex",
                "eth_speed": "speed",
                "eth_media": "media",
                "eth_autoneg": "autoneg",
                "eth_in_flowctrl": "in_flowctrl",
                "eth_out_flowctrl": "out_flowctrl",
                "eth_mdix": "mdix",
                "eth_ratemode": "ratemode",
                "eth_swt_monitor": "swt_monitor",
                "eth_ethertype": "ethertype",
                "eth_eee_state": "eee_state",
                "eth_link_flapped": "link_flapped",
                "eth_clear_counters": "clear_counters",
                "eth_reset_cntr": "reset_cntr",
                "eth_load_interval1_rx": "load_interval1_rx",
                "eth_inrate1_bits": "inrate1_bits",
                "eth_inrate1_pkts": "inrate1_pkts",
                "eth_load_interval1_tx": "load_interval1_tx",
                "eth_outrate1_bits": "outrate1_bits",
                "eth_outrate1_pkts": "outrate1_pkts",
                "eth_inucast": "inucast",
                "eth_inmcast": "inmcast",
                "eth_inbcast": "inbcast",
                "eth_inpkts": "inpkts",
                "eth_inbytes": "inbytes",
                "eth_jumbo_inpkts": "jumbo_inpkts",
                "eth_storm_supp": "storm_supp",
                "eth_runts": "runts",
                "eth_giants": "giants",
                "eth_crc": "crc",
                "eth_nobuf": "nobuf",
                "eth_inerr": "inerr",
                "eth_frame": "frame",
                "eth_overrun": "overrun",
                "eth_underrun": "underrun",
                "eth_ignored": "ignored",
                "eth_watchdog": "watchdog",
                "eth_bad_eth": "bad_eth",
                "eth_bad_proto": "bad_proto",
                "eth_in_ifdown_drops": "in_ifdown_drops",
                "eth_dribble": "dribble",
                "eth_indiscard": "indiscard",
                "eth_inpause": "inpause",
                "eth_outucast": "outucast",
                "eth_outmcast": "outmcast",
                "eth_outbcast": "outbcast",
                "eth_outpkts": "outpkts",
                "eth_outbytes": "outbytes",
                "eth_jumbo_outpkts": "jumbo_outpkts",
                "eth_outerr": "outerr",
                "eth_coll": "coll",
                "eth_deferred": "deferred",
                "eth_latecoll": "latecoll",
                "eth_lostcarrier": "lostcarrier",
                "eth_nocarrier": "nocarrier",
                "eth_babbles": "babbles",
                "eth_outdiscard": "outdiscard",
                "eth_outpause": "outpause",
                "interface": "interface",
                "state_rsn_desc": "state_desc",
                "loop_in_pkts": "inpkts",
                "loop_in_bytes": "inbytes",
                "loop_in_mcast": "inmcast",
                "loop_in_compressed": "incompressed",
                "loop_in_errors": "inerrors",
                "loop_in_frame": "inframe",
                "loop_in_overrun": "inoverrun",
                "loop_in_fifo": "infifo",
                "loop_out_pkts": "outpkts",
                "loop_out_bytes": "outbytes",
                "loop_out_underruns": "outunderruns",
                "loop_out_errors": "outerrors",
                "loop_out_collisions": "outcollisions",
                "loop_out_fifo": "outfifo",
                "loop_out_carriers": "outcarriers",
                "svi_admin_state": "admin_state",
                "svi_rsn_desc": "state_description",
                "svi_line_proto": "line_protocol",
                "svi_mac": "mac",
                "svi_mtu": "mtu",
                "svi_bw": "bw",
                "svi_delay": "delay",
                "svi_tx_load": "tx_load",
                "svi_rx_load": "rx_load",
                "svi_arp_type": "arp_type",
                "svi_time_last_cleared": "last_cleared",
                "svi_ucast_pkts_in": "ucast_pkts_in",
                "svi_ucast_bytes_in": "ucast_bytes_in",
                "vdc_lvl_in_avg_bits": "in_avg_bits",
                "vdc_lvl_in_avg_pkts": "in_avg_pkts",
                "vdc_lvl_out_avg_bits": "out_avg_bits",
                "vdc_lvl_out_avg_pkts": "out_avg_pkts",
                "vdc_lvl_in_pkts": "in_pkts",
                "vdc_lvl_in_ucast": "in_ucast",
                "vdc_lvl_in_mcast": "in_mcast",
                "vdc_lvl_in_bcast": "in_bcast",
                "vdc_lvl_in_bytes": "in_bytes",
                "vdc_lvl_out_pkts": "out_pkts",
                "vdc_lvl_out_ucast": "out_ucast",
                "vdc_lvl_out_mcast": "out_mcast",
                "vdc_lvl_out_bcast": "out_bcast",
                "vdc_lvl_out_bytes": "out_bytes"
            }

    try:
        check_interface = detailed_interface_table.get('interface', None)
    except KeyError:
        return detailed_interface

    if check_interface:
        detailed_interface = apply_key_map(key_map, detailed_interface_table)

    return detailed_interface


def get_resource(device, normalized_interface, interface_type, module):
    interface_dict = get_interfaces_dict(device, module)

    all_interfaces_of_given_type = interface_dict[interface_type]

    if interface_type in ['loopback', 'portchannel', 'svi',
                          'management', 'ethernet']:
        if normalized_interface not in all_interfaces_of_given_type:
            module.fail_json(msg='interface does not exist on device',
                             eth_interfaces=all_interfaces_of_given_type,
                             interface=normalized_interface)
        else:
            resource, mode, interface_table = get_interface(
                                device, normalized_interface, module)

    return resource, mode, interface_table


def get_layer3_info(device, interface, interface_type, module):
    interface_info = {}
    command = 'show ip interface {0}'.format(interface)
    body = parsed_data_from_device(device, command, module)
    interface_table = body['TABLE_intf']['ROW_intf']

    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except KeyError:
        vrf_table = None

    key_map = {
                "prefix": "ip_addr",
                "masklen": "mask",
                "subnet": "subnet",
            }

    interface_info = apply_key_map(key_map, interface_table)
    interface_info['type'] = interface_type
    interface_info['interface'] = interface

    if vrf_table is not None:
        vrf = vrf_table['vrf-name-out']
        interface_info['vrf'] = vrf

    return interface_info


def get_layer2_info(device, port, module):
    """Gets current config of L2 switchport
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        port (str): full name of interface, i.e. Ethernet1/1
    Returns:
        dictionary with k/v pairs for L2 vlan config
    """

    command = 'show interface {0} switchport'.format(port)

    body = parsed_data_from_device(device, command, module)

    if body:
        key_map = {
            "interface": "interface",
            "oper_mode": "mode",
            "switchport": "switchport",
            "access_vlan": "access_vlan",
            "access_vlan_name": "access_vlan_name",
            "native_vlan": "native_vlan",
            "native_vlan_name": "native_vlan_name",
            "trunk_vlans": "trunk_vlans"
        }

        layer2_table = body['TABLE_interface']['ROW_interface']

        layer2_info = apply_key_map(key_map, layer2_table)

        return layer2_info
    else:
        return {}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            interface=dict(required=True),
            detail=dict(choices=BOOLEANS, type='bool'),
            protocol=dict(choices=['http', 'https'], default='http'),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(type='str'),
        ),
        supports_check_mode=False
    )
    if not HAS_PYCSCO:
        module.fail_json(msg='There was a problem loading pycsco')

    auth = Auth(vendor='cisco', model='nexus')
    username = module.params['username'] or auth.username
    password = module.params['password'] or auth.password
    protocol = module.params['protocol']
    detail = module.params['detail'] or False
    host = socket.gethostbyname(module.params['host'])
    interface = module.params['interface'].lower()

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol)

    interface_type = get_interface_type(interface)
    normalized_interface = normalize_interface(interface)

    if interface_type == 'unknown':
        module.fail_json(
            msg='unknown interface type found-1',
            interface=interface)

    resource, mode, interface_table = get_resource(
                    device, normalized_interface, interface_type, module)

    layer3_info = {}
    layer2_info = {}
    oper = {}

    if mode == 'layer3':
        layer3_info = get_layer3_info(
                        device, interface, interface_type, module)
    elif mode == 'layer2':
        layer2_info = get_layer2_info(
                        device, interface, module)

    if detail:
            oper = get_interface_detailed_info(
                                interface_table, interface, module)

    results = {}

    results['resource'] = resource
    results['layer3_info'] = layer3_info
    results['layer2_info'] = layer2_info
    results['oper'] = oper

    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
