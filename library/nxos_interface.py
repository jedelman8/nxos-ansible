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

module: nxos_interface
short_description: Manages physical attributes of interfaces
description:
    - Manages physical attributes on interface of NX-API enabled devices
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - When using one of the five special keywords for the interface
      param, the module is not non-idempotent.  Keywords include all,
      ethernet, loopback, svi, and portchannel.
    - This module is also used to create logical interfaces such as
      svis and loopbacks.
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1, port-channel10.
              Also supports non-idempotent keywords including all, ethernet,
              loopback, svi, portchannel
        required: true
        default: null
        choices: []
        aliases: []
    admin_state:
        description:
            - Administrative state of the interface
        required: false
        default: up
        choices: ['up','down']
        aliases: []
    duplex:
        description:
            - Manage duplex settings on an interface
        required: false
        default: null
        choices: []
        aliases: []
    description:
        description:
            - Interface description
        required: false
        default: null
        choices: []
        aliases: []
    mode:
        description:
            - Manage Layer 2 or Layer 3 state of the interface
        required: false
        default: null
        choices: ['layer2','layer3']
        aliases: []
    speed:
        description:
            - Manage speed settings on an interface
        required: false
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Specify desired state of the resource
        required: true
        default: present
        choices: ['present','absent','default']
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
# Ensure an interface is a Layer 3 port and that it has the proper description
- nxos_interface: interface=Ethernet1/1 description='Configured by Ansible' mode=layer3 host={{ inventory_hostname }}

# Admin down an interface
- nxos_interface: interface=Ethernet2/1 host={{ inventory_hostname }} admin_state=down

# Remove all loopback interfaces
- nxos_interface: interface=loopback state=absent host={{ inventory_hostname }}

# Remove all logical interfaces
- nxos_interface: interface={{ item }} state=absent host={{ inventory_hostname }}
  with_items:
    - loopback
    - portchannel
    - svi

# Admin up all ethernet interfaces
- nxos_interface: interface=ethernet host={{ inventory_hostname }} admin_state=up

# Admin down ALL interfaces (physical and logical)
- nxos_interface: interface=all host={{ inventory_hostname }} admin_state=down

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


def is_default_interface(device, interface, module):
    """Checks to see if interface exists and if it is a default config

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of interface, i.e. vlan10,
            Ethernet1/1, loopback10

    Returns:
        True: if interface has default config
        False: if it does not have a default config
        DNE (str): if the interface does not exist - loopbacks, SVIs, etc.

    """
    command = 'show run interface ' + interface

    try:
        data = device.show(command, text=True)
        data_dict = xmltodict.parse(data[1])
        raw_intf = data_dict['ins_api']['outputs']['output']['body']
        raw_list = raw_intf.split('\n')
        if raw_list[-1].startswith('interface'):
            return True
        else:
            return False
    except (KeyError, CLIError):
        # 'body' won't be there if interface doesn't exist
        # logical interface does not exist
        return 'DNE'


def temp_parsed_data_from_device(device, command):
    try:
        data = device.show(command, text=True)
    except:
        module.fail_json(
            msg='Error sending {0}'.format(command),
            error=str(clie))

    data_dict = xmltodict.parse(data[1])
    body = data_dict['ins_api']['outputs']['output']['body']
    return body


def get_available_features(device, feature, module):
    available_features = {}
    command = 'show feature'
    body = temp_parsed_data_from_device(device, command)

    if body:
        splitted_body = body.split('\n')
        for each in splitted_body[2::]:
            stripped = each.strip()
            words = stripped.split()
            feature = str(words[0])
            state = str(words[2])

            if 'enabled' in state:
                state = 'enabled'
            else:
                state = 'disabled'

            if feature not in available_features.keys():
                available_features[feature] = state
            else:
                if (available_features[feature] == 'disabled' and
                        state == 'enabled'):
                    available_features[feature] = state

    return available_features


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


def get_manual_interface_attributes(device, interface):
    """Gets admin state and description of a SVI interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): full name of SVI interface, i.e. vlan10

    Returns:
        dictionary that has two k/v pairs: admin_state & description
            if not an svi, returns None

    """

    if get_interface_type(interface) == 'svi':
        command = 'show interface ' + interface
        try:
            get_data = device.show(command, text=True)
            data_dict = xmltodict.parse(get_data[1])
            show_command = data_dict['ins_api']['outputs']['output']['body']
        except (KeyError, CLIError):
            return None

        if show_command:
            command_list = show_command.split('\n')
            desc = None
            admin_state = 'up'
            for each in command_list:
                if 'Description:' in each:
                    line = each.split('Description:')
                    desc = line[1].strip().split('MTU')[0].strip()
                elif 'Administratively down' in each:
                    admin_state = 'down'

            return dict(description=desc, admin_state=admin_state)
    else:
        return None


def get_interface(device, intf, module):
    """Gets current config/state of interface

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        intf (string): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20

    Returns:
      dictionary that has relevant config/state data about the given
          interface based on the type of interface it is

    """
    base_key_map = {
        'interface': 'interface',
        'admin_state': 'admin_state',
        'desc': 'description',
    }
    speed_map = {
        'eth_duplex': 'duplex',
        'eth_speed': 'speed',
    }
    mode_map = {
        'eth_mode': 'mode'
    }
    loop_map = {
        'state': 'admin_state'
    }
    svi_map = {
        'svi_admin_state': 'admin_state',
        'desc': 'description'
    }
    mode_value_map = {
        "mode": {
            "access": "layer2",
            "trunk": "layer2",
            "routed": "layer3",
            "layer3": "layer3"
        }
    }

    key_map = {}
    interface = {}

    command = 'show interface ' + intf

    body = parsed_data_from_device(device, command, module)

    if body:
        interface_table = body['TABLE_interface']['ROW_interface']

        intf_type = get_interface_type(intf)
        if intf_type in ['portchannel', 'ethernet']:
            if not interface_table.get('eth_mode'):
                interface_table['eth_mode'] = 'layer3'

        if intf_type == 'ethernet':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            interface.update(temp_dict)

        elif intf_type == 'svi':
            key_map.update(svi_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)
            attributes = get_manual_interface_attributes(device, intf)
            interface['admin_state'] = str(attributes.get('admin_state',
                                                          'nxapibug'))
            interface['description'] = str(attributes.get('description',
                                                          'nxapi_bug'))
        elif intf_type == 'loopback':
            key_map.update(base_key_map)
            key_map.pop('admin_state')
            key_map.update(loop_map)
            temp_dict = apply_key_map(key_map, interface_table)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

        elif intf_type == 'management':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)

        elif intf_type == 'portchannel':
            key_map.update(base_key_map)
            key_map.update(speed_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

    interface['type'] = intf_type

    if interface_table.get('eth_speed'):
        interface['speed'] = get_interface_speed(
            interface_table.get('eth_speed'))

    return interface


def get_interface_speed(speed):
    """Translates speed into bits/sec given the output from the API

    Args:
        speed (string): input should be from NX-API in the form of '10 Gb/s'-
            param being sent should be "eth_speed" from output from
            'show interface eth x/y' in NX-API

    Returns:
        equivalent speed (str) in bits per second or "auto"

    """
    if speed.startswith('auto'):
        return 'auto'
    elif speed.startswith('40'):
        return '40000'
    elif speed.startswith('100 G'):
        return '100000'
    elif speed.startswith('10'):
        return '10000'
    elif speed.startswith('1'):
        return '1000'
    elif speed.startswith('100 M'):
        return '100'


def get_intf_args(interface):
    intf_type = get_interface_type(interface)

    arguments = ['admin_state', 'description']

    if intf_type in ['ethernet', 'management']:
        arguments.extend(['duplex', 'speed'])
    if intf_type in ['ethernet', 'portchannel']:
        arguments.extend(['mode'])

    return arguments


def get_interfaces_dict(device):
    """Gets all active interfaces on a given switch

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py

    Returns:
        dictionary with interface type (ethernet,svi,loop,portchannel) as the
            keys.  Each value is a list of interfaces of given interface (key)
            type.

    """
    command = 'show interface status'
    data = device.show(command)
    data_dict = xmltodict.parse(data[1])
    interfaces = {
        'ethernet': [],
        'svi': [],
        'loopback': [],
        'management': [],
        'portchannel': [],
        'unknown': []
        }

    interface_list = data_dict['ins_api']['outputs']['output']['body'].get(
        'TABLE_interface')['ROW_interface']
    for i in interface_list:
        intf = i['interface']
        intf_type = get_interface_type(intf)

        interfaces[intf_type].append(intf)

    return interfaces


def normalize_interface(if_name):
    """Return the normalized interface name
    """
    def _get_number(if_name):
        digits = ''
        for char in if_name:
            if char.isdigit() or char == '/':
                digits += char
        return digits

    if if_name.lower().startswith('et'):
        if_type = 'Ethernet'
    elif if_name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif if_name.lower().startswith('lo'):
        if_type = 'loopback'
    elif if_name.lower().startswith('po'):
        if_type = 'port-channel'
    else:
        if_type = None

    number_list = if_name.split(' ')
    if len(number_list) == 2:
        number = number_list[-1].strip()
    else:
        number = _get_number(if_name)

    if if_type:
        proper_interface = if_type + number
    else:
        proper_interface = if_name

    return proper_interface


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


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def parsed_data_from_device(device, command, module):

    try:
        data = device.show(command)
    except CLIError as clie:
        module.fail_json(msg='Error sending {0}'.format(command),
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
        return command + ' ; '
    else:
        return ''


def nested_command_list_to_string(command_lists):
    cmds = ''
    if command_lists:
        cmds = ' '.join(' ; '.join(each) + ' ; '
                        for each in command_lists if each)
    return cmds


def get_interface_config_commands(device, interface, intf, existing):
    """Generates list of commands to configure on device

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (str): k/v pairs in the form of a set that should
            be configured on the device
        intf (str): full name of interface, i.e. Ethernet1/1

    Returns:
      list: ordered list of commands to be sent to device

    """

    commands = []

    desc = interface.get('description')
    if desc:
        commands.append('description {0}'.format(desc))

    mode = interface.get('mode')
    if mode:
        if mode == 'layer2':
            command = 'switchport'
        elif mode == 'layer3':
            command = 'no switchport'
        commands.append(command)

    delta_speed = interface.get('speed')
    duplex = interface.get('duplex')

    if delta_speed:
        command = 'speed {0}'.format(delta_speed)
        commands.insert(0, command)

    if duplex:
        if not delta_speed:
            command = 'speed {0}'.format(existing.get('speed'))
            commands.insert(0, command)

        command = 'duplex {0}'.format(duplex)
        commands.append(command)

    admin_state = interface.get('admin_state')
    if admin_state:
        command = get_admin_state(interface, intf, admin_state)
        commands.append(command)

    if commands:
        commands.insert(0, 'interface ' + intf)

    return commands


def get_admin_state(interface, intf, admin_state):
    if admin_state == 'up':
        command = 'no shutdown'
    elif admin_state == 'down':
        command = 'shutdown'
    return command


def get_proposed(existing, normalized_interface, args):

    # gets proper params that are allowed based on interface type
    allowed_params = get_intf_args(normalized_interface)

    proposed = {}

    # retrieves proper interface params from args (user defined params)
    for param in allowed_params:
        temp = args.get(param)
        if temp:
            proposed[param] = temp

    return proposed


def get_existing(device, normalized_interface, module):
    intf_type = get_interface_type(normalized_interface)
    interface_dict = get_interfaces_dict(device)

    all_interfaces_of_given_type = interface_dict[intf_type]

    if intf_type == 'ethernet':
        if normalized_interface not in all_interfaces_of_given_type:
            module.fail_json(msg='interface does not exist on device',
                             eth_interfaces=all_interfaces_of_given_type,
                             interface=normalized_interface)
        else:
            existing = get_interface(device, normalized_interface, module)
    elif intf_type in ['loopback', 'portchannel', 'svi']:
        if normalized_interface not in all_interfaces_of_given_type:
            existing = {}
        else:
            existing = get_interface(device, normalized_interface, module)

    return existing


def main():

    module = AnsibleModule(
        argument_spec=dict(
            interface=dict(required=True),
            admin_state=dict(default='up', choices=['up', 'down']),
            duplex=dict(default=None),
            state=dict(default='present',
                       choices=['present', 'absent', 'default']),
            speed=dict(default=None),
            description=dict(default=None),
            mode=dict(choices=['layer2', 'layer3']),
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

    interface = module.params['interface'].lower()
    duplex = module.params['duplex']
    admin_state = module.params['admin_state']
    speed = module.params['speed']
    description = module.params['description']
    mode = module.params['mode']
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    changed = False

    args = dict(interface=interface, admin_state=admin_state,
                description=description, duplex=duplex, speed=speed, mode=mode)

    intf_type = get_interface_type(interface)

    normalized_interface = normalize_interface(interface)

    if normalized_interface == 'Vlan1' and state == 'absent':
        module.fail_json(msg='CANNOT REMOVE VLAN1.  Doh!')
    elif intf_type in ['management']:
        if state in ['absent', 'default']:
            module.fail_json(msg='CANNOT DEFAULT MGMT0- USED BY NXAPI')

    if intf_type == 'svi':
        feature = 'interface-vlan'
        available_features = get_available_features(device, feature, module)
        svi_state = available_features[feature]
        if svi_state == 'disabled':
            module.fail_json(
                msg='SVI (interface-vlan) feature needs to be enabled first',
            )

    if intf_type == 'unknown':
        module.fail_json(
            msg='unknown interface type found-1',
            interface=interface)

    existing = get_existing(device, normalized_interface, module)

    proposed = get_proposed(existing, normalized_interface, args)

    delta = dict()
    commands = []

    is_default = is_default_interface(device, normalized_interface, module)

    if state == 'absent':
        if intf_type in ['svi', 'loopback', 'portchannel']:
            if is_default != 'DNE':
                cmds = ['no interface {0}'.format(normalized_interface)]
                commands.append(cmds)
        elif intf_type in ['ethernet']:
            if is_default is False:
                cmds = ['default interface {0}'.format(normalized_interface)]
                commands.append(cmds)
    elif state == 'present':
        if not existing:
            cmds = get_interface_config_commands(device, proposed,
                                                 normalized_interface,
                                                 existing)
            commands.append(cmds)
        else:
            delta = dict(set(proposed.iteritems()).difference(
                existing.iteritems()))
            if delta:
                cmds = get_interface_config_commands(device, delta,
                                                     normalized_interface,
                                                     existing)
                commands.append(cmds)
    elif state == 'default':
        if is_default is False:
            cmds = ['default interface {0}'.format(normalized_interface)]
            commands.append(cmds)
        elif is_default == 'DNE':
            module.exit_json(msg='interface you are trying to default does'
                             ' not exist')

    cmds = nested_command_list_to_string(commands)

    end_state = existing

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            device.config(cmds)
            if delta.get('mode'): # or delta.get('admin_state'):
                # if the mode changes from L2 to L3, the admin state
                # changes after the API call, so adding a second API
                # call  just for admin state and using it for a change
                # in admin state or mode.
                admin_state = delta.get('admin_state') or admin_state
                command = get_admin_state(delta, normalized_interface,
                                          admin_state)
                device.config('interface {0} ; {1} ;'.format(normalized_interface,
                                                          command))
                cmds += command
            changed = True
            end_state = get_existing(device, normalized_interface, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed

    module.exit_json(**results)

from ansible.module_utils.basic import *
main()
