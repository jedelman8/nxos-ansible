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

module: nxos_save_config
short_description: Saves running configuration
description:
    - Saves running config to startup-config or file of your choice
author: Jason Edelman (@jedelman8)
requirements:
    - NX-API 1.0
    - NX-OS 6.1(2)I3(1)
    - pycsco
    - xmltodict
notes:
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    path:
        description:
            - Path of destination.  Ex: bootflash:config.cfg, etc.
        required: false
        default: null
        choices: []
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
# save running config to startup-config
- nxos_save_config: host={{ inventory_hostname }}

# save running config to dir in bootflash
- nxos_save_config: path='bootflash:configs/my_config.cfg' host={{ inventory_hostname }}

'''

RETURN = '''
path:
    description: Describes where the running config will be saved
    returned: always
    type: string
    sample: 'startup-config'
status:
    description: Shows whether the save's been successful or not
    returned: always
    type: string
    sample: 'successful'
changed:
    description: Checks to see if a change was made on the device
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
        data = device.show(command, text=True)
    except CLIError as clie:
        module.fail_json(msg='Error sending {}'.format(command),
                         error=str(clie))

    try:
        data_dict = xmltodict.parse(data[1])
        body = data_dict['ins_api']['outputs']['output']['body']
    except KeyError:
        data_dict = xmltodict.parse(data[1])
        error = data_dict['ins_api']['outputs']['output'].get(
            'clierror', 'error1: could not validate save')
        module.fail_json(msg=error)
    return body


def save_config(device, path, module):
    command = 'copy run {0}'.format(path)
    error = None
    changed = False
    complete = False

    save_response = parsed_data_from_device(device, command, module)
    if '100%' in save_response or 'copy complete' in save_response.lower():
        complete = True
        changed = True

    if complete:
        result = 'successful'
        return (result, changed)
    else:
        error = 'error: could not validate save'
        module.fail_json(msg=error, response=save_response)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(default='startup-config'),
            protocol=dict(choices=['http', 'https'], default='http'),
            host=dict(required=True),
            username=dict(type='str'),
            password=dict(type='str'),
        ),
        supports_check_mode=False
    )
    if not HAS_PYCSCO:
        module.fail_json(msg='There was a problem loading pycsco')

    auth = Auth(vendor='cisco', model='nexus')
    username = module.params['username'] or auth.username
    password = module.params['password'] or auth.password
    protocol = module.params['protocol']
    host = socket.gethostbyname(module.params['host'])

    path = module.params['path']

    device = Device(ip=host, username=username, password=password,
                    protocol=protocol)

    if path != 'startup-config':
        if ':' not in path:
            msg = ('invalid format for path.  Requires ":" ' +
                        'Example- bootflash:config.cfg' +
                        'or bootflash:/configs/test.cfg')
            module.fail_json(msg=msg)

    complete_save, changed = save_config(device, path, module)

    results = {}
    results['path'] = path
    results['status'] = complete_save
    results['changed'] = changed

    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
