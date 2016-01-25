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
module: nxos_vrf_interface
short_description: Manages interface specific VRF configuration
description:
    - Manages interface specific VRF configuration
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - VRF needs to be added globally with nxos_vrf before
      adding a VRF to an interface
    - Remove a VRF from an interface will still remove
      all L3 attributes just as it does from CLI
    - VRF is not read from an interface until IP address is
      configured on that interface
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
    interface:
        description:
            - Full name of interface to be managed, i.e. Ethernet1/1
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Manages desired state of the resource
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
# ensure vrf ntc exists on Eth1/1
- nxos_vrf_interface: vrf=ntc interface=Ethernet1/1 host={{ inventory_hostname }} state=present

# ensure ntc VRF does not exist on Eth1/1
- nxos_vrf_interface: vrf=ntc interface=Ethernet1/1 host={{ inventory_hostname }} state=absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"interface": "loopback16", "vrf": "ntc"}
existing:
    description: k/v pairs of existing vrf on the interface
    type: dict
    sample: {"interface": "loopback16", "vrf": ""}
end_state:
    description: k/v pairs of vrf after module execution
    returned: always
    type: dict
    sample: {"interface": "loopback16", "vrf": "ntc"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "interface loopback16 ; vrf member ntc ;"
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


def get_vrf_list(device, module):
    command = 'show vrf all'
    vrf_list = []
    body = parsed_data_from_device(device, command, module)

    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']
        if vrf_table:
            for each in vrf_table:
                vrf_list.append(str(each['vrf_name']))
    except (KeyError, AttributeError):
        return vrf_list

    return vrf_list


def get_interface_info(device, interface, module):
    command = 'show run interface {0}'.format(interface)
    vrf_regex = ".*vrf\s+member\s+(?P<vrf>\S+).*"

    try:
        body = parsed_data_from_device(device, command, module, text=True)
        match_vrf = re.match(vrf_regex, body, re.DOTALL)
        group_vrf = match_vrf.groupdict()
        vrf = group_vrf["vrf"]
    except (AttributeError, CLIError):
        return ""
    return vrf


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vrf=dict(required=True),
            interface=dict(type='str', required=True),
            state=dict(default='present', choices=['present', 'absent']),
            protocol=dict(choices=['http', 'https'], default='http'),
            host=dict(required=True),
            port=dict(required=False, type='int', default=None),
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
    host = socket.gethostbyname(module.params['host'])
    port = module.params['port']

    vrf = module.params['vrf']
    interface = module.params['interface'].lower()
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    current_vrfs = get_vrf_list(device, module)
    if vrf not in current_vrfs:
        module.fail_json(msg="Ensure the VRF you're trying to config/remove on"
                             " an interface is created globally on the device"
                             " first.")

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and
            is_default(device, interface, module) == 'DNE'):
        module.fail_json(msg="interface does not exist on switch. Verify "
                             "switch platform or create it first with "
                             "nxos_interface if it's a logical interface")

    mode = get_interface_mode(device, interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='Ensure interface is a Layer 3 port before '
                             'configuring a VRF on an interface. You can '
                             'use nxos_interface')

    proposed = dict(interface=interface, vrf=vrf)

    current_vrf = get_interface_info(device, interface, module)
    existing = dict(interface=interface, vrf=current_vrf)
    changed = False
    end_state = existing

    if vrf != existing['vrf'] and state == 'absent':
        module.fail_json(msg='The VRF you are trying to remove '
                             'from the interface does not exist '
                             'on that interface.',
                         interface=interface, proposed_vrf=vrf,
                         existing_vrf=existing['vrf'])

    commands = []
    if existing:
        if state == 'absent':
            if existing and vrf == existing['vrf']:
                command = ['no vrf member {0}'.format(vrf)]
                commands.append(command)

        elif state == 'present':
            if existing['vrf'] != vrf:
                command = ['vrf member {0}'.format(vrf)]
                commands.append(command)

    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])
    cmds = nested_command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            changed_vrf = get_interface_info(device, interface, module)
            end_state = dict(interface=interface, vrf=changed_vrf)

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
