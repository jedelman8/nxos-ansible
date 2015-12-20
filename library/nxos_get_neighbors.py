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

module: nxos_get_neighbors
short_description: Gets neighbor detail from a NX-API enabled switch
description:
    - Gets CDP or LLDP information from the switch
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
    type:
        description:
            - Specify neighbor protocol on how information should
              be gathered from switch
        required: true
        default: null
        choices: ['cdp','lldp']
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
        choices: ['http','https']
        aliases: []
'''

EXAMPLES = '''

# retrieve cdp neighbors
- nxos_get_neighbors: type=cdp host={{ inventory_hostname }}

# retrieve lldp neighbors
- nxos_get_neighbors: type=lldp host={{ inventory_hostname }}

'''

RETURN = '''

neighbors:
    description: 
        - information about LLDP/CDP neighbors
    returned: always
    type: list of dict or null
    sample: {"local_interface": "mgmt0", "neighbor": "PERIMETER", 
            "neighbor_interface": "FastEthernet1/0/10"} 

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


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def get_lldp_neighbors(device, module):
    neighbors = []
    command = 'show lldp neighbors'

    body = parsed_data_from_device(device, command, module)
    if body:
        lldp_table = body['TABLE_nbor']['ROW_nbor']

        key_map = {
                "chassis_id": "neighbor",
                "port_id": "neighbor_interface",
                "l_port_id": "local_interface"
            }

        if isinstance(lldp_table, dict):
            lldp_table = [lldp_table]

        for lldp in lldp_table:
            mapped_lldp_neighbor = apply_key_map(key_map, lldp)
            neighbors.append(mapped_lldp_neighbor)
    return neighbors


def get_cdp_neighbors(device, module):
    neighbors = []
    command = 'show cdp neighbors'

    body = parsed_data_from_device(device, command, module)
    if body:
        cdp_table = body['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info']

        key_map = {
                "device_id": "neighbor",
                "port_id": "neighbor_interface",
                "intf_id": "local_interface"
            }

        if isinstance(cdp_table, dict):
            cdp_table = [cdp_table]

        for cdp in cdp_table:
            mapped_cdp_neighbor = apply_key_map(key_map, cdp)
            neighbors.append(mapped_cdp_neighbor)
    return neighbors


def main():
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(choices=['cdp', 'lldp'], required=True),
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
    host = socket.gethostbyname(module.params['host'])

    neighbor_type = module.params['type'].lower()
    device = Device(ip=host, username=username, password=password,
                    protocol=protocol)

    if neighbor_type == 'lldp':
        neighbors = get_lldp_neighbors(device, module)
    elif neighbor_type == 'cdp':
        neighbors = get_cdp_neighbors(device, module)

    results = {}
    results['neighbors'] = neighbors
    module.exit_json(ansible_facts=results)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
