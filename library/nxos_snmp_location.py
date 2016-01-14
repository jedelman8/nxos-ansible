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

module: nxos_snmp_location
short_description: Manages SNMP location information
description:
    - Manages SNMP location configuration
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - state=absent removes the location configuration if it is configured
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    location:
        description:
            - location information
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Manage the state of the resource
        required: true
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
        choices: ['http','https']
        aliases: []
'''

EXAMPLES = '''
# ensure snmp location is configured
- nxos_snmp_location: location=Test state=present host={{ inventory_hostname }}

# ensure snmp location is not configured
nxos_snmp_location: location=Test state=absent host={{ inventory_hostname }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"location": "New_Test"}
existing:
    description: k/v pairs of existing snmp location
    type: dict
    sample: {"location": "Test"}
end_state:
    description: k/v pairs of location info after module execution
    returned: always
    type: dict or null
    sample: {"location": "New_Test"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "snmp-server location New_Test ;"
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


def parsed_data_from_device(device, command, module):

    try:
        data = device.show(command, text=True)
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


def get_snmp_location(device, module):
    """Retrieves snmp location from a device
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
    Returns:
        dictionary
    """
    location = {}
    location_regex = '.*snmp-server\slocation\s(?P<location>\S+).*'
    command = 'show run snmp'

    body = parsed_data_from_device(device, command, module)
    try:
        match_location = re.match(location_regex, body, re.DOTALL)
        group_location = match_location.groupdict()
        location['location'] = group_location["location"]
    except AttributeError:
        location = {}

    return location


def main():
    module = AnsibleModule(
        argument_spec=dict(
            location=dict(required=True, type='str'),
            state=dict(choices=['absent', 'present'],
                       default='present'),
            host=dict(required=True),
            port=dict(required=False, type='int', default=None),
            username=dict(),
            password=dict(),
            protocol=dict(choices=['http', 'https'],
                          default='http')
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

    location = module.params['location']
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    existing = get_snmp_location(device, module)
    changed = False
    commands = []
    proposed = dict(location=location)
    end_state = existing

    if state == 'absent':
        if existing and existing['location'] == location:
            commands.append('no snmp-server location')
    elif state == 'present':
        if not existing or existing['location'] != location:
            commands.append('snmp-server location {0}'.format(location))

    cmds = command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_snmp_location(device, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
