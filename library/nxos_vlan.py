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
module: nxos_vlan
short_description: Manages VLAN resources and attributes
description:
    - Manages VLAN configurations on NX-API enabled switches
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
            - single vlan id
        required: false
        default: null
        choices: []
        aliases: []
    vlan_range:
        description:
            - range of VLANs such as 2-10 or 2,5,10-15, etc.
        required: false
        default: null
        choices: []
        aliases: []
    name:
        description:
            - name of VLAN
        required: false
        default: null
        choices: []
        aliases: []
    vlan_state:
        description:
            - Manage the vlan oper state of the VLAN
              (equiv to state {active | suspend} command
        required: false
        default: active
        choices: ['active','suspend']
        aliases: []
    admin_state:
        description:
            - Manage the vlan admin state of the VLAN equiv to shut/no shut
              in vlan config mode
        required: false
        default: up
        choices: ['up','down']
        aliases: []
    state:
        description:
            - Manage the state of the resource
        required: false
        default: present
        choices: ['present','absent']
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
# Ensure VLAN 50 exists with the name WEB and is in the shutdown state
 - nxos_vlan: vlan_id=50 host={{ inventory_hostname }} admin_state=down name=WEB

# Ensure VLAN is NOT on the device
- nxos_vlan: vlan_id=50 host={{ inventory_hostname }} state=absent

# Ensure a range of VLANs are present on the switch
- nxos_vlan: vlan_id="2-10,20,50,55-60" host={{ inventory_hostname }} state=present

# Ensure a group of VLANs are present with the given names
- nxos_vlan: vlan_id={{ item.vlan_id }} name={{ item.name }} host={{ inventory_hostname }} state=present
  with_items:
    - vlan_id: 10
      name: web
    - vlan_id: 20
      name: app
    - { vlan_id: 30, name: db }
    - vlan_id: 40
      name: misc
    - vlan_id: 99
      name: native_vlan
'''

RETURN = '''

proposed_vlans_list:
    description: list of VLANs being proposed
    returned: always
    type: list
    sample: ["100"]
existing_vlans_list:
    description: list of existing VLANs on the switch prior to making changes
    returned: always
    type: list
    sample: ["1", "2", "3", "4", "5", "20"]
end_state_vlans_list:
    description: list of VLANs after the module is executed
    returned: always
    type: list
    sample:  ["1", "2", "3", "4", "5", "20", "100"]
proposed:
    description: k/v pairs of parameters passed into module (does not include
                 vlan_id or vlan_range)
    returned: always
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan",
            "vlan_state": "suspend"}
existing:
    description: k/v pairs of existing vlan or null when using vlan_range
    returned: always
    type: dict
    sample: {"admin_state": "down", "name": "app_vlan",
             "vlan_id": "20", "vlan_state": "suspend"}
end_state:
    description: k/v pairs of the VLAN after executing module or null
                 when using vlan_range
    returned: always
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan", "vlan_id": "20",
             "vlan_state": "suspend"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "vlan 20 ; vlan 55 ;"
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true

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


def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return numerical_sort(result)
    return result


def numerical_sort(string_int_list):
    """Sorts list of strings/integers that are digits in numerical order.
    """

    as_int_list = []
    as_str_list = []
    for vlan in string_int_list:
        as_int_list.append(int(vlan))
    as_int_list.sort()
    for vlan in as_int_list:
        as_str_list.append(str(vlan))
    return as_str_list


def build_commands(vlans, state):
    commands = []
    for vlan in vlans:
        if state == 'present':
            command = 'vlan {}'.format(vlan)
            commands.append(command)
        elif state == 'absent':
            command = 'no vlan {}'.format(vlan)
            commands.append(command)
    return commands


def get_vlan_config_commands(vlan, vid):
    """Build command list required for VLAN configuration
    """

    reverse_value_map = {
        "admin_state": {
            "down": "shutdown",
            "up": "no shutdown"
        }
    }

    if vlan.get('admin_state'):
        # do we need to apply the value map?
        # only if we are making a change to the admin state
        # would need to be a loop or more in depth check if
        # value map has more than 1 key
        vlan = apply_value_map(reverse_value_map, vlan)

    VLAN_ARGS = {
        'name': 'name {name}',
        'vlan_state': 'state {vlan_state}',
        'admin_state': '{admin_state}',
        'mode': 'mode {mode}'
    }

    commands = []

    for param, value in vlan.iteritems():
        command = VLAN_ARGS.get(param).format(**vlan)
        if command:
            commands.append(command)

    commands.insert(0, 'vlan ' + vid)
    commands.append('exit')

    return commands


def get_list_of_vlans(device, module):

    command = 'show vlan'

    body = parsed_data_from_device(device, command, module)

    vlan_list = []

    if body:
        vlan_table = body.get('TABLE_vlanbrief')['ROW_vlanbrief']

        vlan_list = []
        if isinstance(vlan_table, list):
            for vlan in vlan_table:
                vlan_list.append(str(vlan['vlanshowbr-vlanid-utf']))
        else:
            vlan_list.append('1')

    return vlan_list


def get_vlan(device, vlanid, module):
    """Get instance of VLAN as a dictionary
    """

    command = 'show vlan id ' + vlanid

    body = parsed_data_from_device(device, command, module)

    if body:
        vlan_table = body['TABLE_vlanbriefid']['ROW_vlanbriefid']

        key_map = {
            "vlanshowbr-vlanid-utf": "vlan_id",
            "vlanshowbr-vlanname": "name",
            "vlanshowbr-vlanstate": "vlan_state",
            "vlanshowbr-shutstate": "admin_state"
        }

        vlan = apply_key_map(key_map, vlan_table)

        value_map = {
            "admin_state": {
                "shutdown": "down",
                "noshutdown": "up"
            }
        }

        vlan = apply_value_map(value_map, vlan)

    else:
        # VLAN DOES NOT EXIST
        return {}

    return vlan


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


def parsed_data_from_device(device, command, module):

    try:
        data = device.show(command)
    except CLIError as clie:
        module.fail_json(msg='Error sending {}'.format(command),
                         error=str(clie))

    data_dict = xmltodict.parse(data[1])
    body = data_dict['ins_api']['outputs']['output']['body']

    return body


def command_list_to_string(command_list):
    """Converts list of commands into proper string for NX-API

    Args:
        cmds (list): ordered list of commands

    Returns:
        str: string of commands separated by " ; "

    """
    if command_list:
        command = ' ; '.join(command_list)
        return command + ' ;'
    else:
        return ''


def nested_command_list_to_string(command_lists):
    cmds = ''
    if command_lists:
        cmds = ' '.join(' ; '.join(each) + ' ;'
                        for each in command_lists if each)
    return cmds


def main():

    module = AnsibleModule(
        argument_spec=dict(
            vlan_id=dict(required=False, type='str'),
            vlan_range=dict(required=False),
            name=dict(required=False),
            vlan_state=dict(choices=['active', 'suspend'], required=False),
            state=dict(choices=['present', 'absent'], default='present'),
            admin_state=dict(choices=['up', 'down'], required=False),
            protocol=dict(choices=['http', 'https'], default='http'),
            port=dict(required=False, type='int', default=None),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(type='str'),
        ),
        mutually_exclusive=[['vlan_range', 'name'],
                            ['vlan_id', 'vlan_range']],
        supports_check_mode=True
    )

    if not HAS_PYCSCO:
        module.fail_json(msg='There was a problem loading pycsco')

    auth = Auth(vendor='cisco', model='nexus')
    username = module.params['username'] or auth.username
    password = module.params['password'] or auth.password
    protocol = module.params['protocol']
    port = module.params['port']
    host = socket.gethostbyname(module.params['host'])

    vlan_range = module.params['vlan_range']
    vlan_id = module.params['vlan_id']
    name = module.params['name']
    vlan_state = module.params['vlan_state']
    admin_state = module.params['admin_state']
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    changed = False

    if vlan_id:
        if not vlan_id.isdigit():
            module.fail_json(msg='vlan_id must be a valid VLAN ID')

    args = dict(name=name, vlan_state=vlan_state,
                admin_state=admin_state)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    proposed_vlans_list = numerical_sort(vlan_range_to_list(
        vlan_id or vlan_range))
    existing_vlans_list = numerical_sort(get_list_of_vlans(device, module))

    commands = []
    existing = None

    if vlan_range:
        if state == 'present':
            # These are all of the VLANs being proposed that don't
            # already exist on the switch
            vlans_delta = list(
                set(proposed_vlans_list).difference(existing_vlans_list))
            commands = build_commands(vlans_delta, state)
        elif state == 'absent':
            # VLANs that are common between what is being proposed and
            # what is on the switch
            vlans_common = list(
                set(proposed_vlans_list).intersection(existing_vlans_list))
            commands = build_commands(vlans_common, state)
    else:
        existing = get_vlan(device, vlan_id, module)
        if state == 'absent':
            if existing:
                commands = ['no vlan ' + vlan_id]
        elif state == 'present':
            delta = dict(set(
                proposed.iteritems()).difference(existing.iteritems()))
            if delta or not existing:
                commands = get_vlan_config_commands(delta, vlan_id)

    end_state = existing
    end_state_vlans_list = existing_vlans_list

    cmds = command_list_to_string(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            try:
                device.config(cmds)
            except CLIError as clie:
                module.fail_json(msg='Error sending CLI commands',
                                 error=str(clie), commands=cmds)
            changed = True
            end_state_vlans_list = numerical_sort(get_list_of_vlans(device, module))
            if vlan_id:
                end_state = get_vlan(device, vlan_id, module)

    results = {}
    results['proposed_vlans_list'] = proposed_vlans_list
    results['existing_vlans_list'] = existing_vlans_list
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['end_state_vlans_list'] = end_state_vlans_list
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed

    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
