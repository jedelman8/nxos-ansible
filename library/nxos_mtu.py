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

module: nxos_mtu
short_description: Manages MTU settings on Nexus switch
description:
    - Manages MTU settings on Nexus switch
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - Either sysmtu param is required or interface AND mtu params are req'd
    - Absent unconfigures a given MTU if that value is currently present
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1
        required: false
        default: null
        choices: []
        aliases: []
    mtu:
        description:
            - MTU for a specific interface
        required: false
        default: null
        choices: []
        aliases: []
    sysmtu:
        description:
            - System jumbo MTU
        required: false
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Specify desired state of the resource
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
        choices: ['http', 'https']
        aliases: []
'''

EXAMPLES = '''
# Ensure system mtu is 9126
- nxos_mtu: sysmtu=9216 host={{ inventory_hostname }}

# Config mtu on Eth1/1 (routed interface)
- nxos_mtu: interface=Ethernet1/1 mtu=1600 host={{ inventory_hostname }}

# Config mtu on Eth1/3 (switched interface)
- nxos_mtu: interface=Ethernet1/3 mtu=9216 host={{ inventory_hostname }}

# Unconfigure mtu on a given interface
- nxos_mtu: interface=Ethernet1/3 mtu=9216 host={{ inventory_hostname }} state=absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mtu": "1700"}
existing:
    description:
        - k/v pairs of existing mtu/sysmtu on the interface/system
    type: dict
    sample: {"mtu": "1600", "sysmtu": "9216"}
end_state:
    description: k/v pairs of mtu/sysmtu values after module execution
    returned: always
    type: dict
    sample: {"mtu": "1700", sysmtu": "9216"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "interface vlan10 ; mtu 1700 ;"
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


def parsed_data_from_device(device, command, module, text=False):
    try:
        data = device.show(command, text=text)
    except CLIError as clie:
        if 'show run interface' in command:
            return 'DNE'
        else:
            module.fail_json(msg='Error sending {0}'.format(command),
                             error=str(clie))

    data_dict = xmltodict.parse(data[1])
    body = data_dict['ins_api']['outputs']['output']['body']

    return body


def nested_command_list_to_string(command_lists):
    cmds = ''
    if command_lists:
        cmds = ' '.join(' ; '.join(each) + ' ;'
                        for each in command_lists if each)
    return cmds


def get_mtu(device, interface, module):
    command = 'show interface {0}'.format(interface)
    mtu = {}

    body = parsed_data_from_device(device, command, module)

    try:
        mtu_table = body['TABLE_interface']['ROW_interface']
        mtu['mtu'] = str(
            mtu_table.get('eth_mtu',
                          mtu_table.get('svi_mtu', 'unreadable_via_api')))
        mtu['sysmtu'] = get_system_mtu(device, module)['sysmtu']
    except KeyError:
        mtu = {}

    return mtu


def get_system_mtu(device, module):
    command = 'show run all | inc jumbomtu'

    body = parsed_data_from_device(device, command, module, text=True)
    sysmtu = str(body.split(' ')[-1])
    try:
        sysmtu = int(sysmtu)
    except:
        sysmtu = ""

    return dict(sysmtu=str(sysmtu))


def get_commands_config_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'mtu {mtu}',
        'sysmtu': 'system jumbomtu {sysmtu}',
    }

    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


def get_commands_remove_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'no mtu {mtu}',
        'sysmtu': 'no system jumbomtu {sysmtu}',
    }
    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


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


def is_default(device, interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = parsed_data_from_device(device, command,
                                       module, text=True)
        if body == 'DNE':
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except (KeyError):
        return 'DNE'


def get_interface_mode(device, interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    interface = {}
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = parsed_data_from_device(device, command, module)
        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'loopback' or intf_type == 'svi':
        mode = 'layer3'
    return mode


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mtu=dict(type='str'),
            interface=dict(type='str'),
            sysmtu=dict(type='str'),
            state=dict(choices=['absent', 'present'], default='present'),
            protocol=dict(choices=['http', 'https'], default='http'),
            port=dict(required=False, type='int', default=None),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(type='str'),
        ),
        required_together=[['mtu', 'interface']],
        supports_check_mode=True
    )
    if not HAS_PYCSCO:
        module.fail_json(msg='pycsco is required for this module')

    auth = Auth(vendor='cisco', model='nexus')
    username = module.params['username'] or auth.username
    password = module.params['password'] or auth.password
    protocol = module.params['protocol']
    port = module.params['port']
    host = socket.gethostbyname(module.params['host'])

    interface = module.params['interface']
    mtu = module.params['mtu']
    sysmtu = module.params['sysmtu']
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    if sysmtu and (interface or mtu):
        module.fail_json(msg='Proper usage-- either just use the sysmtu param '
                             'or use interface AND mtu params')

    if interface:
        intf_type = get_interface_type(interface)
        if intf_type != 'ethernet':
            if is_default(device, interface, module) == 'DNE':
                module.fail_json(msg='Invalid interface.  It does not exist '
                                     'on the switch.')

        existing = get_mtu(device, interface, module)
    else:
        existing = get_system_mtu(device, module)

    if interface and mtu:
        if intf_type == 'loopback':
            module.fail_json(msg='Cannot set MTU for loopback interface.')
        mode = get_interface_mode(device, interface, intf_type, module)
        if mode == 'layer2':
            if intf_type in ['ethernet', 'portchannel']:
                if mtu not in [existing['sysmtu'], '1500']:
                    module.fail_json(msg='MTU on L2 interfaces can only be set'
                                         ' to the system default (1500) or '
                                         'existing sysmtu value which is '
                                         ' {0}'.format(existing['sysmtu']))
        elif mode == 'layer3':
            if intf_type in ['ethernet', 'portchannel', 'svi']:
                if ((int(mtu) < 576 or int(mtu) > 9216) or
                        ((int(mtu) % 2) != 0)):
                    module.fail_json(msg='Invalid MTU for Layer 3 interface'
                                         'needs to be an even number between'
                                         '576 and 9216')
    if sysmtu:
        if ((int(sysmtu) < 576 or int(sysmtu) > 9216 or
                ((int(sysmtu) % 2) != 0))):
                    module.fail_json(msg='Invalid MTU- needs to be an even '
                                         'number between 576 and 9216')

    args = dict(mtu=mtu, sysmtu=sysmtu)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        if delta:
            command = get_commands_config_mtu(delta, interface)
            commands.append(command)

    elif state == 'absent':
        common = set(proposed.iteritems()).intersection(existing.iteritems())
        if common:
            command = get_commands_remove_mtu(dict(common), interface)
            commands.append(command)

    cmds = nested_command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            if interface:
                end_state = get_mtu(device, interface, module)
            else:
                end_state = get_system_mtu(device, module)

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
