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

module: nxos_feature
short_description: Manage features in NX-API enabled devices
description:
    - Offers ability to enable and disable features in NX-OS
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
notes:
    - feature name must match that from the CLI
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    feature:
        description:
            - Name of feature
        required: true
        default: null
        choices: []
        aliases: []
    state:
        description:
            - Desired state of the feature
        required: true
        default: null
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
# Ensure lacp is enabled
- nxos_feature: feature=lacp state=enabled host={{ inventory_hostname }}

# Ensure ospf is disabled
- nxos_feature: feature=ospf state=disabled host={{ inventory_hostname }}

# Ensure vpc is enabled
- nxos_feature: feature=vpc state=enabled host={{ inventory_hostname }}

'''

RETURN = '''

proposed:
    description: proposed feature state
    returned: always
    type: dict
    sample: {"state": "disabled"}
existing:
    description: existing state of feature
    returned: always
    type: dict
    sample: {"state": "enabled"}
end_state:
    description: feature state after executing module
    returned: always
    type: dict
    sample: {"state": "disabled"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "disabled"
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "no feature eigrp ;"
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


def temp_parsed_data_from_device(device, command):
    try:
        data = device.show(command, text=True)
    except:
        module.fail_json(
            msg='Error sending {}'.format(command),
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

            if feature not in available_features.keys():
                available_features[feature] = state
            else:
                if (available_features[feature] == 'disabled' and
                        state == 'enabled'):
                    available_features[feature] = state

    return available_features


def get_commands(proposed, existing, state, feature):
    commands = []
    feature_check = proposed == existing
    if not feature_check:
        if state == 'enabled':
            command = 'feature {0}'.format(feature)
            commands.append(command)
        elif state == 'disabled':
            command = "no feature {0}".format(feature)
            commands.append(command)
    cmds = command_list_to_string(commands)
    return cmds


def main():
    results = {}
    module = AnsibleModule(
        argument_spec=dict(
            feature=dict(type='str', required=True),
            state=dict(choices=['enabled', 'disabled'], required=True),
            protocol=dict(choices=['http', 'https'], default='http'),
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
    host = socket.gethostbyname(module.params['host'])

    feature = module.params['feature'].lower()
    state = module.params['state'].lower()

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol)

    available_features = get_available_features(device, feature, module)

    if feature not in available_features.keys():
        module.fail_json(
            msg='Invalid feature name.',
            features_currently_supported=available_features,
            invalid_feature=feature)
    else:
        existstate = available_features[feature]

        existing = dict(state=existstate)
        proposed = dict(state=state)
        changed = False
        end_state = existing

        cmds = get_commands(proposed, existing, state, feature)

        if cmds:
            changed = True
            device.config(cmds)
            updated_features = get_available_features(device, feature, module)
            existstate = updated_features[feature]
            end_state = dict(state=existstate)

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
