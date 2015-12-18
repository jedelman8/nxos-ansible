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

module: nxos_switchport
short_description: Manages Layer 2 switchport interfaces
description:
    - Manages Layer 2 interfaces
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - When state=absent, vlans can be added/removed from trunk links and and
      the existing access vlan can be 'unconfigured' from the interface
    - When working with trunks VLANs the keywords add/remove are always sent
      in the switchport trunk allowed vlan command.
    - When state=unconfigured, the interface will result with having a default
      Layer 2 interface, i.e. vlan 1 in access mode
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    interface:
        description:
            - Full name of the interface, i.e. Ethernet1/1
        required: true
        default: null
        choices: []
        aliases: []
    mode:
        description:
            - Mode for the Layer 2 port
        required: null
        default: null
        choices: ['access','trunk']
        aliases: []
    access_vlan:
        description:
            - if mode=access, used as the access vlan id
        required: false
        default: null
        choices: []
        aliases: []
    native_vlan:
        description:
            - if mode=trunk, used as the trunk native vlan id
        required: false
        default: null
        choices: []
        aliases: []
    trunk_vlans:
        description:
            - if mode=trunk, used as the vlan range to ADD or REMOVE
              from the trunk
        required: false
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Manage the state of the resource.
        required: null
        default:  present
        choices: ['present','absent', 'unconfigured']
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
# ENSURE Eth1/5 is in its default switchport state
 - nxos_switchport: interface=eth1/5 state=unconfigured host={{ inventory_hostname }}

# ENSURE Eth1/5 is configured for access vlan 20
- nxos_switchport: interface=eth1/5 mode=access access_vlan=20 host={{ inventory_hostname }}

# Ensure eth1/5 is a trunk port and ensure 2-50 are being tagged (doesn't mean others aren't also being tagged)
- nxos_switchport: interface=eth1/5 mode=trunk native_vlan=10 trunk_vlans=2-50 host={{ inventory_hostname }}

# Ensure these VLANs are not being tagged on the trunk
- nxos_switchport: interface=eth1/5 mode=trunk trunk_vlans=51-4094 host={{ inventory_hostname }} state=absent

'''

RETURN = '''

proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"access_vlan": "10", "interface": "eth1/5", "mode": "access"}
existing:
    description: k/v pairs of existing switchport
    type: dict
    sample:  {"access_vlan": "10", "access_vlan_name": "VLAN0010",
              "interface": "Ethernet1/5", "mode": "access",
              "native_vlan": "1", "native_vlan_name": "default",
              "switchport": "Enabled", "trunk_vlans": "1-4094"}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample:  {"access_vlan": "10", "access_vlan_name": "VLAN0010",
              "interface": "Ethernet1/5", "mode": "access",
              "native_vlan": "1", "native_vlan_name": "default",
              "switchport": "Enabled", "trunk_vlans": "1-4094"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "interface eth1/5 ; switchport access vlan 20 ;"
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true

'''


import socket
try:
    HAS_PYCSCO = True
    from pycsco.nxos.device import Device
    from pycsco.nxos.device import Auth
    from pycsco.nxos.error import CLIError
    import xmltodict
except ImportError as ie:
    HAS_PYCSCO = False


def get_interface_type(interface):
    """Gets the type of interface

    Args:
        interface (str): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20

    Returns:
        type of interface: ethernet, svi, loopback, management, portchannel,
         or unknown

    """
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


def get_interface_mode(device, interface, module):
    """Gets current mode of interface: layer2 or layer3

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (string): full name of interface, i.e. Ethernet1/1,
            loopback10, port-channel20, vlan20

    Returns:
        str: 'layer2' or 'layer3'

    """
    command = 'show interface ' + interface

    intf_type = get_interface_type(interface)

    body = parsed_data_from_device(device, command, module)

    mode = 'unknown'
    if body:
        try:
            interface_table = body['TABLE_interface']['ROW_interface']
        except (KeyError, AttributeError, CLIError):
            pass
    if interface_table:
        if intf_type in ['ethernet', 'portchannel']:
            mode = str(interface_table.get('eth_mode', 'layer3'))
            if mode in ['access', 'trunk']:
                mode = 'layer2'
            if mode == 'routed':
                mode = 'layer3'
        elif intf_type == 'loopback' or intf_type == 'svi':
            mode = 'layer3'
    return mode


def interface_is_portchannel(device, interface, module):
    """Checks to see if an interface is part of portchannel bundle

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. Ethernet1/1

    Returns:
        True/False based on if interface is a member of a portchannel bundle

    """
    intf_type = get_interface_type(interface)
    if intf_type == 'ethernet':
        command = 'show interface ' + interface
        body = parsed_data_from_device(device, command, module)
        try:
            interface_table = body['TABLE_interface']['ROW_interface']
        except (KeyError, AttributeError, CLIError):
            interface_table = None
        if interface_table:
            state = interface_table.get('eth_bundle')
            if state:
                return True
            else:
                return False

    return False


def get_switchport(device, port, module):
    """Gets current config of L2 switchport

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        port (str): full name of interface, i.e. Ethernet1/1

    Returns:
        dictionary with k/v pairs for L2 vlan config

    """

    command = 'show interface {0} switchport'.format(port)

    body = parsed_data_from_device(device, command, module)

    if body:
        key_map = {
            "interface": "interface",
            "oper_mode": "mode",
            "switchport": "switchport",
            "access_vlan": "access_vlan",
            "access_vlan_name": "access_vlan_name",
            "native_vlan": "native_vlan",
            "native_vlan_name": "native_vlan_name",
            "trunk_vlans": "trunk_vlans"
        }

        sp_table = body['TABLE_interface']['ROW_interface']

        sp = apply_key_map(key_map, sp_table)

        return sp
    else:
        return {}


def remove_switchport_config_commands(interface, existing, proposed):
    mode = proposed.get('mode')
    commands = []
    command = None
    if mode == 'access':
        av_check = existing.get('access_vlan') == proposed.get('access_vlan')
        if av_check:
            command = 'no switchport access vlan {}'.format(
                existing.get('access_vlan'))
            commands.append(command)
    elif mode == 'trunk':
        tv_check = existing.get('trunk_vlans_list') == proposed.get('trunk_vlans_list')
        if not tv_check:
            vlans_to_remove = False
            for vlan in proposed.get('trunk_vlans_list'):
                if vlan in existing.get('trunk_vlans_list'):
                    vlans_to_remove = True
                    break
            if vlans_to_remove:
                command = 'switchport trunk allowed vlan remove {}'.format(
                    proposed.get('trunk_vlans'))
                commands.append(command)
        native_check = existing.get(
            'native_vlan') == proposed.get('native_vlan')
        if native_check and proposed.get('native_vlan'):
            command = 'no switchport trunk native vlan {}'.format(
                existing.get('native_vlan'))
            commands.append(command)
    if commands:
        commands.insert(0, 'interface ' + interface)
    return commands


def get_switchport_config_commands(interface, existing, proposed):
    """Gets commands required to config a given switchport interface
    """

    proposed_mode = proposed.get('mode')
    existing_mode = existing.get('mode')

    commands = []
    command = None
    if proposed_mode != existing_mode:
        if proposed_mode == 'trunk':
            command = 'switchport mode trunk'
        elif proposed_mode == 'access':
            command = 'switchport mode access'
    if command:
        commands.append(command)

    if proposed_mode == 'access':
        av_check = existing.get('access_vlan') == proposed.get('access_vlan')
        if not av_check:
            command = 'switchport access vlan {}'.format(
                proposed.get('access_vlan'))
            commands.append(command)
    elif proposed_mode == 'trunk':
        tv_check = existing.get('trunk_vlans_list') == proposed.get('trunk_vlans_list')
        if not tv_check:
            vlans_to_add = False
            for vlan in proposed.get('trunk_vlans_list'):
                if vlan not in existing.get('trunk_vlans_list'):
                    vlans_to_add = True
                    break
            if vlans_to_add:
                command = 'switchport trunk allowed vlan add {}'.format(proposed.get('trunk_vlans'))
                commands.append(command)

        native_check = existing.get(
            'native_vlan') == proposed.get('native_vlan')
        if not native_check and proposed.get('native_vlan'):
            command = 'switchport trunk native vlan {}'.format(
                proposed.get('native_vlan'))
            commands.append(command)
    if commands:
        commands.insert(0, 'interface ' + interface)
    return commands


def is_switchport_default(existing):
    """Determines if switchport has a default config based on mode

    Args:
        existing (dict): existing switcport configuration from Ansible mod

    Returns:
        boolean: True if switchport has OOB Layer 2 config, i.e.
           vlan 1 and trunk all and mode is access

    """

    c1 = existing['access_vlan'] == '1'
    c2 = existing['native_vlan'] == '1'
    c3 = existing['trunk_vlans'] == '1-4094'
    c4 = existing['mode'] == 'access'

    default = c1 and c2 and c3 and c4

    return default


def default_switchport_config(interface):
    commands = []
    commands.append('interface ' + interface)
    commands.append('switchport mode access')
    commands.append('switch access vlan 1')
    commands.append('switchport trunk native vlan 1')
    commands.append('switchport trunk allowed vlan all')
    return commands


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
            interface=dict(required=True, type='str'),
            mode=dict(choices=['access', 'trunk']),
            access_vlan=dict(type='str', required=False),
            native_vlan=dict(type='str', required=False),
            trunk_vlans=dict(type='str', required=False),
            state=dict(choices=['absent', 'present', 'unconfigured'],
                       default='present'),
            protocol=dict(choices=['http', 'https'], default='http'),
            host=dict(required=True),
            username=dict(required=False),
            password=dict(required=False),
        ),
        mutually_exclusive=[['access_vlan', 'trunk_vlans'],
                            ['access_vlan', 'native_vlan']],
        supports_check_mode=True
    )

    if not HAS_PYCSCO:
        module.fail_json(msg='There was a problem loading pycsco')

    auth = Auth(vendor='cisco', model='nexus')
    username = module.params['username'] or auth.username
    password = module.params['password'] or auth.password
    protocol = module.params['protocol']
    host = socket.gethostbyname(module.params['host'])

    interface = module.params['interface']
    mode = module.params['mode']
    access_vlan = module.params['access_vlan']
    state = module.params['state']
    trunk_vlans = module.params['trunk_vlans']
    native_vlan = module.params['native_vlan']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol)

    args = dict(interface=interface, mode=mode, access_vlan=access_vlan,
                native_vlan=native_vlan, trunk_vlans=trunk_vlans)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    interface = interface.lower()

    if mode == 'access' and state == 'present' and not access_vlan:
        module.fail_json(msg='access_vlan param is required when '
                         'mode=access && state=present')

    if mode == 'trunk' and access_vlan:
        module.fail_json(msg='access_vlan param not supported when '
                         'using mode=trunk')

    current_mode = get_interface_mode(device, interface, module)

    # Current mode will return layer3, layer2, or unknown
    if current_mode == 'unknown' or current_mode == 'layer3':
        module.fail_json(msg='Ensure interface is configured to be a L2'
                         '\nport first before using this module. You can use'
                         '\nthe nxos_interface module for this.')

    if interface_is_portchannel(device, interface, module):
        module.fail_json(msg='Cannot change L2 config on physical '
                         '\nport because it is in a portchannel. '
                         '\nYou should update the portchannel config.')

    # existing will never be null for Eth intfs as there is always a default
    existing = get_switchport(device, interface, module)

    # Safeguard check
    # If there isn't an existing, something is wrong per previous comment
    if not existing:
        module.fail_json(msg='Make sure you are using the FULL interface name')

    current_vlans = get_list_of_vlans(device, module)

    if state == 'present':
        if access_vlan and access_vlan not in current_vlans:
            module.fail_json(msg='You are trying to configure a VLAN'
                             ' on an interface that\ndoes not exist on the '
                             ' switch yet!', vlan=access_vlan)
        elif native_vlan and native_vlan not in current_vlans:
            module.fail_json(msg='You are trying to configure a VLAN'
                             ' on an interface that\ndoes not exist on the '
                             ' switch yet!', vlan=native_vlan)

    if trunk_vlans:
        trunk_vlans_list = vlan_range_to_list(trunk_vlans)

        existing_trunks_list = vlan_range_to_list(
            (existing['trunk_vlans'])
            )

        existing['trunk_vlans_list'] = existing_trunks_list
        proposed['trunk_vlans_list'] = trunk_vlans_list

    changed = False

    commands = []

    if state == 'present':
        command = get_switchport_config_commands(interface, existing, proposed)
        commands.append(command)
    elif state == 'unconfigured':
        is_default = is_switchport_default(existing)
        if not is_default:
            command = default_switchport_config(interface)
            commands.append(command)
    elif state == 'absent':
        command = remove_switchport_config_commands(interface,
                                                    existing, proposed)
        commands.append(command)

    if trunk_vlans:
        existing.pop('trunk_vlans_list')
        proposed.pop('trunk_vlans_list')

    end_state = existing

    cmds = nested_command_list_to_string(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_switchport(device, interface, module)

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
