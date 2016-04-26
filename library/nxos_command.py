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

module: nxos_command
short_description: Send raw commands to Cisco NX-API enabled devices
description:
    - Raw show and config commands can be sent to NX-API enabled devices.
      For show commands there is the ability to return structured
      or raw text data.
      The command param when type=config can be a list or string with commands
      separated by a comma.
author: Jason Edelman (@jedelman8)
notes:
    - Only a single show command can be sent per task while multiple
      config commands can be sent.
    - Single show command or list of config commands or series of config
      commands separated by a comma supported
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
options:
    command:
        description:
            - Show command as a string or a string of config commands
              separated by a comma
        required: false
        default: null
        choices: []
        aliases: []
    command_list:
        description:
            - Config commands as a list
        required: false
        default: null
        choices: []
        aliases: []
    type:
        description:
            - Represents the type of command being sent to the device
        required: true
        default: null
        choices: ['show','config']
        aliases: []
    text:
        description:
            - Dictates how data will be returned for show commands.
              Set to true if NX-API doesn't support structured output
              for a given command. Doesn't work for config commands.
        required: false
        default: null
        choices: [true,false]
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
# Get CLI raw text output for a given command
- nxos_command: command='show run interface mgmt0 | inc description' host={{ inventory_hostname }} text=true type=show

# Get structured JSON data for given command
- nxos_command: command='show interface Ethernet1/1' host={{ inventory_hostname }} type=show

# Configure secondary interface on Eth1/2 with command as string
- nxos_command: command='interface Eth1/2 ; ip address 5.5.5.5/24 secondary ;' host={{ inventory_hostname }} type=config

# Configure secondary interface on Eth1/2 with command as list
- nxos_command:
    host: "{{ inventory_hostname }}"
    type: config
    command_list: ['interface Eth1/2','ip address 5.3.3.5/24 secondary']
'''

RETURN = '''

proposed:
    description: proposed changes
    returned: always
    type: dict
    sample: {"cmd_type":"config",
            "commands":"interface lo13, ip add 13.13.13.13 255.255.255.0"
            }
commands:
    description:
        - Command list sent to device. This's ALWAY a list.
    returned: always
    type: list
    sample: ["interface lo13, ip add 13.13.13.13 255.255.255.0"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
result:
    description: show the outcome of our commands
    returned: always
    type: dict
    sample: {"changed":false,"commands": "show hostname",
            "proposed": {"cmd_type": "show","commands": "show hostname",
            "text": null},"response": [{"body": {"hostname": "N9K2"},
            "code": "200","input": "show hostname", "msg": "Success"}]}}
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


def normalize_to_list(output):
    if isinstance(output, dict):
        return [output]
    else:
        return output


def parsed_data_from_device(device, command, module, text):
    try:
        data = device.show(command, text=text)
    except CLIError as clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))

    data_dict = xmltodict.parse(data[1])

    output = normalize_to_list(data_dict['ins_api']['outputs']['output'])

    return output


def send_config_command(device, command, module):
    try:
        data = device.config(command)
    except CLIError as clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))

    data_dict = xmltodict.parse(data[1])

    output = normalize_to_list(data_dict['ins_api']['outputs']['output'])

    return output


def send_show_command(device, command, module, text):
    if text is None:
        text = False
    return parsed_data_from_device(device, command, module, text)


def command_list_to_string(command_list):
    """Converts list of commands into proper string for NX-API
    Args:
        cmds (list): ordered list of commands
    Returns:
        str: string of commands separated by " ; "
    """
    if command_list:
        command = ' ; '.join(command_list)
        return command
    else:
        return ''


def main():

    module = AnsibleModule(
        argument_spec=dict(
            command=dict(required=False),
            command_list=dict(required=False),
            text=dict(choices=BOOLEANS, type='bool'),
            type=dict(choices=['show', 'config'], required=True),
            protocol=dict(choices=['http', 'https'], default='http'),
            port=dict(required=False, type='int', default=None),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(no_log=True, type='str')
        ),
        required_one_of=[['command', 'command_list']],
        mutually_exclusive=[['command', 'command_list']],
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

    command = module.params['command']
    command_list = module.params['command_list']
    text = module.params['text'] or None
    cmd_type = module.params['type'].lower()

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    changed = False
    cmds = ''

    if command:
        if isinstance(command, str):
            cmds = command_list_to_string([command])
        else:
            module.fail_json(msg='Only strings are supported with "command"'
                             '\nIf you want to use a list, use the param'
                             '" command_list" instead.')

    elif command_list:
        if isinstance(command_list, list):
            cmds = command_list_to_string(command_list)
        else:
            module.fail_json(msg='Only Lists are supported with "command_list"'
                             '\nIf you want to send a single command,'
                             'use the param "command" instead.')

    proposed = dict(commands=cmds, text=text, cmd_type=cmd_type)

    if cmds:
        if cmd_type == 'show':
            response = send_show_command(device, cmds, module, text)

        elif cmd_type == 'config':
            changed = True
            response = send_config_command(device, cmds, module)
    else:
        module.fail_json(msg='no commands to send. check format')

    results = {}
    results['changed'] = changed
    results['proposed'] = proposed
    results['commands'] = cmds
    results['response'] = response

    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
