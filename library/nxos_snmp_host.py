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

module: nxos_snmp_host
short_description: Manages SNMP host configuration
description:
    - Manages SNMP host configuration parameters
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - state=absent removes the host configuration if it is configured
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    snmp_host:
        description:
            - IP address of hostname of target host
        required: true
        default: null
        choices: []
        aliases: []
    version:
        description:
            - SNMP version
        required: false
        default: v2c
        choices: ['v2c', 'v3']
        aliases: []
    community:
        description:
            - Community string or v3 username
        required: false
        default: null
        choices: []
        aliases: []
    udp:
        description:
            - UDP port number (0-65535)
        required: false
        default: null
        choices: []
        aliases: []
    type:
        description:
            - type of message to send to host
        required: false
        default: traps
        choices: ['trap', 'inform']
        aliases: []
    vrf:
        description:
            - VRF to use to source traffic to source
        required: false
        default: null
        choices: []
        aliases: []
    vrf_filter:
        description:
            - Name of VRF to filter
        required: false
        default: null
        choices: []
        aliases: []
    src_intf:
        description:
            - Source interface
        required: false
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
# ensure snmp host is configured
- nxos_snmp_host: snmp_host=3.3.3.3 community=TESTING state=present host={{ inventory_hostname }}

# ensure snmp host is no configured
- nxos_snmp_host: snmp_host=3.3.3.3 community=TESTING state=absent host={{ inventory_hostname }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"community": "TESTING", "snmp_host": "3.3.3.3", 
            "snmp_type": "trap", "version": "v2c", "vrf_filter": "one_more_vrf"}
existing:
    description: k/v pairs of existing snmp host
    type: dict
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf"]}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf", "one_more_vrf"]}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "snmp-server host 3.3.3.3 filter-vrf another_test_vrf ;"
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


def get_snmp_host(device, host, module):
    """Retrieves snmp host configuration for a given host on a given device
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class
        host (str): IP Address or hostname of snmp host
    Returns:
        dictionary
    """
    command = 'show snmp host'
    body = parsed_data_from_device(device, command, module)

    host_map = {
        'port': 'udp',
        'version': 'version',
        'level': 'v3',
        'type': 'snmp_type',
        'secname': 'community'
    }

    resource = {}

    try:
        resource_table = body['TABLE_host']['ROW_host']

        if isinstance(resource_table, dict):
            resource_table = [resource_table]

        for each in resource_table:
            key = str(each['host'])
            src = each.get('src_intf', None)
            host_resource = apply_key_map(host_map, each)

            if src:
                host_resource['src_intf'] = src.split(':')[1].strip()

            vrf_filt = each.get('TABLE_vrf_filters', None)
            if vrf_filt:
                vrf_filter = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')
                filters = [vrf.strip() for vrf in vrf_filter]
                host_resource['vrf_filter'] = filters

            vrf = each.get('vrf', None)
            if vrf:
                host_resource['vrf'] = vrf.split(':')[1].strip()
            resource[key] = host_resource

    except (KeyError, AttributeError):
        return resource

    find = resource.get(host, None)
    if find:
        return find
    else:
        return {}


def remove_snmp_host(host, existing):
    commands = []
    if existing['version'] == 'v3':
        existing['version'] = '3'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {v3} {community}'.format(host, **existing)

    elif existing['version'] == 'v2c':
        existing['version'] = '2c'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {community}'.format(host, **existing)

    if command:
        commands.append(command)
    return commands


def config_snmp_host(delta, proposed, existing, module):
    commands = []
    command_builder = []
    host = proposed['snmp_host']
    cmd = 'snmp-server host {0}'.format(proposed['snmp_host'])

    snmp_type = delta.get('snmp_type', None)
    version = delta.get('version', None)
    ver = delta.get('v3', None)
    community = delta.get('community', None)

    command_builder.append(cmd)
    if any([snmp_type, version, ver, community]):
        type_string = snmp_type or existing.get('type')
        if type_string:
            command_builder.append(type_string)

        version = version or existing.get('version')
        if version:
            if version == 'v2c':
                vn = '2c'
            elif version == 'v3':
                vn = '3'

            version_string = 'version {0}'.format(vn)
            command_builder.append(version_string)

        if ver:
            ver_string = ver or existing.get('v3')
            command_builder.append(ver_string)

        if community:
            community_string = community or existing.get('community')
            command_builder.append(community_string)

        cmd = ' '.join(command_builder)

        commands.append(cmd)

    CMDS = {
        'vrf_filter': 'snmp-server host {0} filter-vrf {vrf_filter}',
        'vrf': 'snmp-server host {0} use-vrf {vrf}',
        'udp': 'snmp-server host {0} udp-port {udp}',
        'src_intf': 'snmp-server host {0} source-interface {src_intf}'
    }

    for key, value in delta.iteritems():
        if key in ['vrf_filter', 'vrf', 'udp', 'src_intf']:
            command = CMDS.get(key, None)
            if command:
                cmd = command.format(host, **delta)
                commands.append(cmd)
            cmd = None
    return commands


def main():
    module = AnsibleModule(
        argument_spec=dict(
            snmp_host=dict(required=True, type='str'),
            community=dict(type='str'),
            udp=dict(type='str'),
            version=dict(choices=['v2c', 'v3'],
                         default='v2c'),
            src_intf=dict(type='str'),
            v3=dict(choices=['noauth', 'auth', 'priv']),
            vrf_filter=dict(type='str'),
            vrf=dict(type='str'),
            snmp_type=dict(choices=['trap', 'inform'],
                           default='trap'),
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

    snmp_host = module.params['snmp_host']
    community = module.params['community']
    udp = module.params['udp']
    version = module.params['version']
    src_intf = module.params['src_intf']
    v3 = module.params['v3']
    vrf_filter = module.params['vrf_filter']
    vrf = module.params['vrf']
    snmp_type = module.params['snmp_type']

    state = module.params['state']

    if snmp_type == 'inform' and version != 'v3':
        module.fail_json(msg='inform requires snmp v3')

    if version == 'v2c' and v3:
        module.fail_json(msg='param: "v3" should not be used when '
                             'using version v2c')

    if not any([vrf_filter, vrf, udp, src_intf]):
        if not all([snmp_type, version, community]):
            module.fail_json(msg='when not configuring options like '
                                 'vrf_filter, vrf, udp, and src_intf,'
                                 'the following params are required: '
                                 'type, version, community')

    if version == 'v3' and v3 is None:
        module.fail_json(msg='when using version=v3, the param v3 '
                             '(options: auth, noauth, priv) is also required')

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol, port=port)

    existing = get_snmp_host(device, snmp_host, module)

    # existing returns the list of vrfs configured for a given host
    # checking to see if the proposed is in the list
    store = existing.get('vrf_filter', None)
    if existing and store:
        if vrf_filter not in existing['vrf_filter']:
            existing['vrf_filter'] = None
        else:
            existing['vrf_filter'] = vrf_filter

    args = dict(
            community=community,
            snmp_host=snmp_host,
            udp=udp,
            version=version,
            src_intf=src_intf,
            vrf_filter=vrf_filter,
            v3=v3,
            vrf=vrf,
            snmp_type=snmp_type
            )

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    commands = []
    end_state = existing

    if state == 'absent':
        if existing:
            command = remove_snmp_host(snmp_host, existing)
            commands.append(command)
    elif state == 'present':
        if delta:
            command = config_snmp_host(delta, proposed, existing, module)
            commands.append(command)

    cmds = nested_command_list_to_string(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_snmp_host(device, snmp_host, module)

    if store:
        existing['vrf_filter'] = store

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['end_state'] = end_state
    results['commands'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()