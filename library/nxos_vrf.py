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
module: nxos_vrf
short_description: Manages global VRF configuration
description:
    - Manages global VRF configuration
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
    vrf:
        description:
            - Name of VRF to be managed
        required: true
        default: null
        choices: []
        aliases: []
    admin_state:
        description:
            - Administrative state of the VRF
        required: false
        default: up
        choices: ['up','down']
        aliases: []
    state:
        description:
            - Manages desired state of the resource
        required: true
        default: present
        choices: ['present','absent']
        aliases: []
    description:
        description:
            - Description of the VRF
        required: false
        default: null
        choices: []
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
# ensure ntc VRF exists on switch
- nxos_vrf: vrf=ntc host={{ inventory_hostname }}

# ensure ntc VRF does not exist on switch
- nxos_vrf: vrf=ntc host={{ inventory_hostname }} state=absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"admin_state": "Up", "description": "Test test",
            "vrf": "ntc"}
existing:
    description: k/v pairs of existing vrf
    type: dict
    sample: {"admin_state": "Up", "description": "Old test",
            "vrf": "old_ntc"}
end_state:
    description: k/v pairs of vrf info after module execution
    returned: always
    type: dict
    sample: {"admin_state": "Up", "description": "Test test",
            "vrf": "ntc"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "vrf context ntc ; no shutdown ; description Test test ;"
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import socket
import xmltodict
import re
try:
    HAS_PYCSCO = True
    from pycsco.nxos.device import Device
    from pycsco.nxos.device import Auth
    from pycsco.nxos.error import CLIError
except ImportError as ie:
    HAS_PYCSCO = False


def parsed_data_from_device(device, command, module, text=False):
    try:
        data = device.show(command, text=text)
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


def nested_command_list_to_string(command_lists):
    cmds = ''
    if command_lists:
        cmds = ' '.join(' ; '.join(each) + ' ;'
                        for each in command_lists if each)
    return cmds


def get_commands_to_config_vrf(delta, vrf):
    commands = []
    for param, value in delta.iteritems():
        command = ''
        if param == 'description':
            command = 'description {0}'.format(value)
        elif param == 'admin_state':
            if value.lower() == 'up':
                command = 'no shutdown'
            elif value.lower() == 'down':
                command = 'shutdown'
        if command:
            commands.append(command)
    if commands:
        commands.insert(0, 'vrf context {0}'.format(vrf))
    return commands


def get_vrf_description(device, vrf, module):
    command = ('show run section vrf | begin {0} '
               '| include description'.format(vrf))

    description = ''
    descr_regex = r".*description\s(?P<descr>[\S+\s]+).*"
    body = parsed_data_from_device(device, command, module, text=True)

    if body:
        try:
            match_description = re.match(descr_regex, body, re.DOTALL)
            group_description = match_description.groupdict()
            description = group_description["descr"]
        except AttributeError:
            description = ''

    return description


def get_vrf(device, vrf, module):
    command = 'show vrf {0}'.format(vrf)
    parsed_vrf = {}

    vrf_key = {
        'vrf_name': 'vrf',
        'vrf_state': 'admin_state'
        }

    body = parsed_data_from_device(device, command, module)

    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']

        parsed_vrf = apply_key_map(vrf_key, vrf_table)
        parsed_vrf['description'] = get_vrf_description(
                                        device, parsed_vrf['vrf'], module)
    except TypeError:
        return parsed_vrf

    return parsed_vrf


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vrf=dict(required=True),
            admin_state=dict(default='up', choices=['up', 'down']),
            state=dict(default='present', choices=['present', 'absent']),
            description=dict(default=None),
            protocol=dict(choices=['http', 'https'], default='http'),
            port=dict(required=False, type='int', default=None),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(type='str'),
        ),
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

    vrf = module.params['vrf']
    admin_state = module.params['admin_state'].lower()
    description = module.params['description']
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    if vrf == 'default':
        module.fail_json(msg='cannot use default as name of a VRF')

    existing = get_vrf(device, vrf, module)

    args = dict(vrf=vrf, description=description,
                admin_state=admin_state)

    end_state = existing
    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    if existing:
        if existing['admin_state'].lower() == admin_state:
            proposed['admin_state'] = existing['admin_state']

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
    changed = False
    end_state = existing
    commands = []
    if state == 'absent':
        if existing:
            command = ['no vrf context {0}'.format(vrf)]
            commands.append(command)

    elif state == 'present':
        if not existing:
            command = get_commands_to_config_vrf(delta, vrf)
            commands.append(command)
        elif delta:
                command = get_commands_to_config_vrf(delta, vrf)
                commands.append(command)

    cmds = nested_command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_vrf(device, vrf, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
