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
module: nxos_get_vlan
short_description: Gets VLAN facts about Nexus NX-API enabled switch
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
    vlan_id:
        description:
            - Vlan ID of target vlan
        required: true
        default: 'all'
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
# retrieve all vlan facts
- nxos_get_vlan: host={{ inventory_hostname }}
# retrieve facts of a specific vlan
- nxos_get_vlan:  vlan_id=10 host={{ inventory_hostname }}
'''

RETURN = '''
vlan_facts:
    description:
        - Show multiple information about vlans.
    returned: always
    type: dict or list of dicts
    sample: {"admin_state": "noshutdown", "interfaces": [
            "port-channel11-12", "Ethernet1/5", "Ethernet1/6",
            "Ethernet1/7", "Ethernet2/5", "Ethernet2/6"],
            "name": "test_segment", "state": "active",
            "vlan_id": "10"}
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
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


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
            vlan_id=dict(required=False, default='all'),
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

    vlan_id = module.params['vlan_id']

    try:
        vlan_id = int(vlan_id)
    except ValueError:
        if vlan_id != 'all':
            module.fail_json(msg='The value {0} is not a '
                                 'valid Vlan ID. This should be '
                                 'an integer or "all".'.format(vlan_id))

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    show_vlan_command = 'show vlan brief'

    show_vlan_body = parsed_data_from_device(device, show_vlan_command, module)
    vlan_facts = get_vlan_facts(show_vlan_body)

    if isinstance(vlan_id, int):
        present = False
        for each in vlan_facts:
            if int(each['vlan_id']) == vlan_id:
                present = True
                vlan_facts = each
        if not present:
            vlan_facts = {}

    module.exit_json(vlan_facts=vlan_facts)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()