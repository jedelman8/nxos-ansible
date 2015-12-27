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


def parsed_data_from_device(device, command, module):
    try:
        data = device.show(command)
    except CLIError as clie:
        module.fail_json(msg='Error sending {}'.format(command),
                         error=str(clie))

    data_dict = xmltodict.parse(data[1])
    body = data_dict['ins_api']['outputs']['output']['body']
    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = str(value)
    return new_dict


def get_interface_type(interface):
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


def get_interface_detailed_info(device, interface, module):
    detailed_interface = {}
    command = 'show interface {0}'.format(interface)
    body = parsed_data_from_device(device, command, module)
    detailed_interface_table = body['TABLE_interface']['ROW_interface']

    key_map = {
                "state": "state",
                "admin_state": "admin_state",
                "share_state": "share_state",
                "eth_hw_desc": "hw_desc",
                "eth_hw_addr": "hw_addr",
                "eth_bia_addr": "bia_addr",
                "description": "description",
                "eth_mtu": "mtu",
                "bw": "bw",
                "dly": "delay",
                "reliability": "reliability",
                "eth_txload": "tx_load",
                "rx_txload": "rx_load",
                "medium": "medium",
                "eth_mode": "mode",
                "eth_duplex": "duplex",
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
                "interface": "interface"
            }

    check_interface = detailed_interface_table.get('interface', None)
    if check_interface:
        detailed_interface = apply_key_map(key_map, detailed_interface_table)

    return detailed_interface


def get_interface_info(device, interface, interface_type, module):
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

    if interface_type != 'ethernet':
        module.fail_json(msg='module only currently supported for Ethernet '
                         'interface.  Use nxapi_command for others.')
    else:
        if detail:
            get_data = get_interface_detailed_info(device, interface, module)
        else:
            get_data = get_interface_info(
                            device, interface, interface_type, module)

    results = {}
    results['interface'] = get_data

    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
