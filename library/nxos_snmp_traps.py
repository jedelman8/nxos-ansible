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

module: nxos_snmp_trap
short_description: Manages SNMP traps
description:
    - Manages SNMP traps configurations
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - This module works at the group level for traps.  If you need to only
      enable/disable 1 specific trap within a group, use the nxos_command
      module.

      IMPORTANT: Be aware that you can set a trap only for an enabled feature.

    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    group:
        description:
            - Case sensitive group
        required: true
        default: null
        choices: ['aaa', 'bridge', 'callhome', 'cfs', 'config', 'entity',
          'feature-control', 'hsrp', 'license', 'link', 'lldp', 'ospf', 'pim',
          'rf', 'rmon', 'snmp', 'storm-control', 'stpx', 'sysmgr', 'system',
          'upgrade', 'vtp', 'all']
        aliases: []
    state:
        description:
            - Manage the state of the resource
        required: true
        default: present
        choices: ['enabled','disabled']
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
# ensure lldp trap configured
- nxos_snmp_traps: group=lldp state=enabled host={{ inventory_hostname }}

# ensure lldp trap is not configured
- nxos_snmp_traps: group=lldp state=disabled host={{ inventory_hostname }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "lldp"}
existing:
    description: k/v pairs of existing trap status
    type: dict
    sample: {"lldp": [{"enabled": "No",
            "trap": "lldpRemTablesChange"}]}
end_state:
    description: k/v pairs of trap info after module execution
    returned: always
    type: dict
    sample: {"lldp": [{"enabled": "Yes",
            "trap": "lldpRemTablesChange"}]}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "enabled"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "snmp-server enable traps lldp ;"
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


def get_snmp_traps(device, group, module):
    """Retrieves snmp traps configuration for a given device
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        group (str): group of snmp traps as defined in the switch
    Returns:
        list
    """
    command = 'show snmp trap'
    body = parsed_data_from_device(device, command, module)

    trap_key = {
        'description': 'trap',
        'isEnabled': 'enabled'
    }

    resource = {}

    try:
        resource_table = body['TABLE_snmp_trap']['ROW_snmp_trap']

        for each_feature in ['aaa', 'bridge', 'callhome', 'cfs', 'config',
                             'entity', 'feature-control', 'hsrp', 'license',
                             'link', 'lldp', 'ospf', 'pim', 'rf', 'rmon',
                             'snmp', 'storm-control', 'stpx', 'sysmgr',
                             'system', 'upgrade', 'vtp']:

            resource[each_feature] = []

        for each_resource in resource_table:
            key = str(each_resource['trap_type'])
            mapped_trap = apply_key_map(trap_key, each_resource)

            if key != 'Generic':
                resource[key].append(mapped_trap)

    except (KeyError, AttributeError):
        return resource

    find = resource.get(group, None)

    if group == 'all'.lower():
        return resource
    elif find:
        trap_resource = {group: resource[group]}
        return trap_resource
    else:
        # if 'find' is None, it means that 'group' is a
        # currently disabled feature.
        return {}


def get_trap_commands(group, state, existing, module):
    commands = []
    enabled = False
    disabled = False

    if group == 'all':
        if state == 'disabled':
            for feature in existing:
                trap_commands = ['no snmp-server enable traps {0}'.format(feature) for
                                    trap in existing[feature] if trap['enabled'] == 'Yes']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

        elif state == 'enabled':
            for feature in existing:
                trap_commands = ['snmp-server enable traps {0}'.format(feature) for
                                    trap in existing[feature] if trap['enabled'] == 'No']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

    else:
        if group in existing:
            for each_trap in existing[group]:
                check = each_trap['enabled']
                if check.lower() == 'yes':
                    enabled = True
                if check.lower() == 'no':
                    disabled = True

            if state == 'disabled' and enabled:
                commands.append(['no snmp-server enable traps {0}'.format(group)])
            elif state == 'enabled' and disabled:
                commands.append(['snmp-server enable traps {0}'.format(group)])
        else:
            module.fail_json(msg='{0} is not a currently '
                                 'enabled feature.'.format(group))

    return commands


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['enabled', 'disabled'], required=True),
            group=dict(choices=['aaa', 'bridge', 'callhome', 'cfs', 'config',
                                'entity', 'feature-control', 'hsrp',
                                'license', 'link', 'lldp', 'ospf', 'pim', 'rf',
                                'rmon', 'snmp', 'storm-control', 'stpx',
                                'sysmgr', 'system', 'upgrade', 'vtp', 'all'],
                       required=True),
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
    host = socket.gethostbyname(module.params['host'])
    port = module.params['port']

    group = module.params['group'].lower()
    state = module.params['state']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    existing = get_snmp_traps(device, group, module)
    proposed = {'group': group}

    changed = False
    end_state = existing
    commands = get_trap_commands(group, state, existing, module)

    cmds = nested_command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_snmp_traps(device, group, module)

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
