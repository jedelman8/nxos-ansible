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

module: nxos_snmp_community
short_description: Manages SNMP community configs
description:
    - Manages SNMP community configuration
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
    community:
        description:
            - Case-sensitive community string
        required: true
        default: null
        choices: []
        aliases: []
    access:
        description:
            - Access type for community
        required: false
        default: null
        choices: ['ro','rw']
        aliases: []
    group:
        description:
            - Group to which the community belongs
        required: false
        default: null
        choices: []
        aliases: []
    acl:
        description:
            - acl name to filter snmp requests
        required: false
        default: 1
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
# ensure snmp community is configured
- nxos_snmp_community: community=TESTING7 group=network-operator state=present host={{ inventory_hostname }}

# ensure snmp community is not configured
- nxos_snmp_community: community=TESTING7 group=network-operator state=absent host={{ inventory_hostname }}

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "network-operator"}
existing:
    description: k/v pairs of existing snmp community
    type: dict
    sample:  {}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample:  {"acl": "None", "group": "network-operator"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "snmp-server community TESTING7 group network-operator ;"
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


def nested_command_list_to_string(command_lists):
    cmds = ''
    if command_lists:
        cmds = ' '.join(' ; '.join(each) + ' ;'
                        for each in command_lists if each)
    return cmds


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


def get_snmp_groups(device, module):
    """Retrieves snmp groups for a given device
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
    Returns:
        list of groups
    """
    command = 'show snmp group'
    data = parsed_data_from_device(device, command, module)

    group_list = []

    try:
        group_table = data['TABLE_role']['ROW_role']
        for group in group_table:
            group_list.append(group['role_name'])
    except (KeyError, AttributeError):
        return group_list
    return group_list


def get_snmp_community(device, module, find_filter=None):
    """Retrieves snmp community settings for a given device
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        community (str): optional arg to filter out this specific community
    Returns:
        dictionary
    """
    command = 'show snmp community'
    data = parsed_data_from_device(device, command, module)

    community_dict = {}

    community_map = {
        'grouporaccess': 'group',
        'aclfilter': 'acl'
    }

    try:
        community_table = data['TABLE_snmp_community']['ROW_snmp_community']
        for each in community_table:
            community = apply_key_map(community_map, each)
            key = each['community_name']
            community_dict[key] = community
    except (KeyError, AttributeError):
        return community_dict

    if find_filter:
        find = community_dict.get(find_filter, None)

    if find_filter is None or find is None:
        return {}
    else:
        return find


def config_snmp_community(delta, community):
    CMDS = {
        'group': 'snmp-server community {0} group {group}',
        'acl': 'snmp-server community {0} use-acl {acl}'
    }
    commands = []
    for k, v in delta.iteritems():
        cmd = CMDS.get(k).format(community, **delta)
        if cmd:
            commands.append(cmd)
            cmd = None
    return commands


def main():
    module = AnsibleModule(
        argument_spec=dict(
            community=dict(required=True, type='str'),
            access=dict(choices=['ro', 'rw']),
            group=dict(type='str'),
            acl=dict(type='str'),
            state=dict(choices=['absent', 'present'],
                       default='present'),
            host=dict(required=True),
            port=dict(required=False, type='int', default=None),
            username=dict(),
            password=dict(),
            protocol=dict(choices=['http', 'https'],
                          default='http')
        ),
        required_one_of=[['access', 'group']],
        mutually_exclusive=[['access', 'group']],
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

    access = module.params['access']
    group = module.params['group']
    community = module.params['community']
    acl = module.params['acl']
    state = module.params['state']

    if access:
        if access == 'ro':
            group = 'network-operator'
        elif access == 'rw':
            group = 'network-admin'

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    # group check - ensure group being configured exists on the device
    configured_groups = get_snmp_groups(device, module)

    if group not in configured_groups:
        module.fail_json(msg="group not on switch."
                         "please add before moving forward")

    existing = get_snmp_community(device, module, community)
    args = dict(group=group, acl=acl)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    end_state = existing
    commands = []

    if state == 'absent':
        if existing:
            command = "no snmp-server community {}".format(community)
            commands.append(command)
        cmds = command_list_to_string(commands)
    elif state == 'present':
        if delta:
            command = config_snmp_community(dict(delta), community)
            commands.append(command)
        cmds = nested_command_list_to_string(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_snmp_community(device, module, community)

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
