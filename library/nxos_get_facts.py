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

module: nxos_get_facts
short_description: Gets facts about Nexus NX-API enabled switch
description:
    - Offers ability to extract facts from device
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    detail:
        description:
            - if set to true, returns detailed statistics for interfaces
              equivalent to 'show interface status'
        required: false
        default: false
        choices: ['true','false']
        aliases: []
    host:
        description:
            - IP Address or hostname (resolvable by Ansible control host)
              of the target NX-API enabled switch
        required: true
        default: null
        choices: []
        aliases: []
    port:
        description:
            - TCP port to use for communication with switch
        required: false
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
# retrieve facts
- nxos_get_facts: host={{ inventory_hostname }}


'''

RETURN = '''
facts:
    description:
        - Show multiple information about device.
          These include interfaces, vlans, module and environment information.
    returned: always
    type: dict
    sample: {"fan_info": [{"direction":"front-to-back","hw_ver": "--",
            "model":"N9K-C9300-FAN2","name":"Fan1(sys_fan1)","status":"Ok"}],
            "hostname": "N9K2","interfaces": ["mgmt0","Ethernet1/1"],
            "kickstart": "6.1(2)I3(1)","module": [{"model": "N9K-C9396PX",
            "ports": "48","status": "active *"}],"os": "6.1(2)I3(1)",
            "platform": "Nexus9000 C9396PX Chassis","power_supply_info": [{
            "actual_output": "0 W","model": "N9K-PAC-650W","number": "1",
            "status":"Shutdown"}],"rr":"Reset Requested by CLI command reload",
            "vlan_list":[{"admin_state":"noshutdown","interfaces":["Ethernet1/1"],
            "name": "default","state": "active","vlan_id": "1"}]}
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
        module.fail_json(msg='Error sending {0}'.format(command),
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


def get_show_version_facts(body):
    key_map = {
                "rr_sys_ver": "os",
                "kickstart_ver_str": "kickstart",
                "chassis_id": "platform",
                "host_name": "hostname",
                "rr_reason": "rr"
            }

    mapped_show_version_facts = apply_key_map(key_map, body)
    return mapped_show_version_facts


def get_interface_facts(body, detail):
    detailed_list = []
    interface_list = []
    detailed_table = body['TABLE_interface']['ROW_interface']

    key_map = {
                "description": "description",
                "state": "state",
                "chassis_id": "platform",
                "vlan": "vlan",
                "duplex": "duplex",
                "speed": "speed",
                "type": "type"
            }

    if isinstance(detailed_table, dict):
        detailed_table = [detailed_table]

    for each in detailed_table:
        interface = str(each.get('interface', None))
        if interface:
            temp = {}
            temp['interface'] = interface
            interface_list.append(interface)
            if detail:
                mapped_detailed_facts = apply_key_map(key_map, each)
                mapped_detailed_facts.update(temp)
                detailed_list.append(mapped_detailed_facts)
    return (detailed_list, interface_list)


def get_show_module_facts(body):
    module_facts = []
    module_table = body['TABLE_modinfo']['ROW_modinfo']

    key_map = {
                "ports": "ports",
                "type": "type",
                "model": "model",
                "status": "status"
            }

    if isinstance(module_table, dict):
        module_table = [module_table]

    for each in module_table:
        mapped_module_facts = apply_key_map(key_map, each)
        module_facts.append(mapped_module_facts)
    return module_facts


def get_powersupply_facts(body):
    powersupply_facts = []
    powersupply_table = body['powersup']['TABLE_psinfo']['ROW_psinfo']

    key_map = {
                "psnum": "number",
                "psmodel": "model",
                "actual_out": "actual_output",
                "actual_in": "actual_input",
                "total_capa": "total_capacity",
                "ps_status": "status"
            }

    if isinstance(powersupply_table, dict):
        powersupply_table = [powersupply_table]

    for each in powersupply_table:
        mapped_powersupply_facts = apply_key_map(key_map, each)
        powersupply_facts.append(mapped_powersupply_facts)
    return powersupply_facts


def get_fan_facts(body):
    fan_facts = []
    fan_table = body['fandetails']['TABLE_faninfo']['ROW_faninfo']

    key_map = {
                "fanname": "name",
                "fanmodel": "model",
                "fanhwver": "hw_ver",
                "fandir": "direction",
                "fanstatus": "status"
            }

    if isinstance(fan_table, dict):
        fan_table = [fan_table]

    for each in fan_table:
        mapped_fan_facts = apply_key_map(key_map, each)
        fan_facts.append(mapped_fan_facts)
    return fan_facts


def get_vlan_facts(body):
    vlan_facts = []
    vlan_table = body['TABLE_vlanbriefxbrief']['ROW_vlanbriefxbrief']

    key_map = {
                "vlanshowbr-vlanid-utf": "vlan_id",
                "vlanshowbr-vlanname": "name",
                "vlanshowbr-shutstate": "admin_state",
                "vlanshowbr-vlanstate": "state",
                "vlanshowplist-ifidx": "interfaces"
            }

    if isinstance(vlan_table, dict):
        vlan_table = [vlan_table]

    for each in vlan_table:
        mapped_vlan_facts = apply_key_map(key_map, each)
        try:
            if mapped_vlan_facts['interfaces']:
                mapped_vlan_facts['interfaces'] = mapped_vlan_facts['interfaces'].split(',')
        except KeyError:
            mapped_vlan_facts['interfaces'] = []
        vlan_facts.append(mapped_vlan_facts)
    return vlan_facts


def main():

    module = AnsibleModule(
        argument_spec=dict(
            protocol=dict(choices=['http', 'https'], default='http'),
            port=dict(required=False, type='int', default=None),
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
    port = module.params['port']
    host = socket.gethostbyname(module.params['host'])

    detail = module.params['detail']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    show_version_command = 'show version'
    interface_command = 'show interface status'
    show_module_command = 'show module'
    show_environment_command = 'show environment'
    show_vlan_command = 'show vlan brief'

    # Get 'show version' facts.
    show_version_body = parsed_data_from_device(device, show_version_command, module)
    show_version = get_show_version_facts(show_version_body)

    # Get interfaces facts.

    try:
        interface_body = parsed_data_from_device(device, interface_command, module)
        detailed_list, interface_list = get_interface_facts(interface_body, detail)
    except:
        # 7K hack for now
        interface_list = []

    # Get module facts.
    show_module_body = parsed_data_from_device(
                                    device, show_module_command, module)
    show_module = get_show_module_facts(show_module_body)

    # Get environment facts.
    show_environment_body = parsed_data_from_device(
                                    device, show_environment_command, module)
    powersupply = get_powersupply_facts(show_environment_body)
    fan = get_fan_facts(show_environment_body)

    # Get vlans facts.
    show_vlan_body = parsed_data_from_device(device, show_vlan_command, module)
    vlan = get_vlan_facts(show_vlan_body)

    facts = dict(
        interfaces=interface_list,
        module=show_module,
        power_supply_info=powersupply,
        fan_info=fan,
        vlan_list=vlan)

    facts.update(show_version)

    module.exit_json(ansible_facts=facts)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
