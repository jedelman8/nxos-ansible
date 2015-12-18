The intent of this document is to provide some high level guidelines on how to migrate off of the `pycsco` library for these Ansible modules.  To further clarify, we will still be using the `Device` object and errors from `pycsco`,just not any of the _helper functions_.  There are various reasons for doing this, some of which I can cover offline if you want to know more.


# REFERENCE

The two modules migrated so far are nxos_switchport.py and nxos_switchport.py

They can be found here:

[https://github.com/jedelman8/nxos-ansible/tree/modules-no-pycsco-utils/library](https://github.com/jedelman8/nxos-ansible/tree/modules-no-pycsco-utils/library)

Okay, here we go.

# Add `if __name__ == "__main__":` into each module

The current modules have this:

```python
from ansible.module_utils.basic import *
main()
```

We want this:

```python
from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
```


# Rename the module to have a `.py` file extension

# RESULTS

* Think about the `results` being returned - do we want to return more data??   I think we are good for most, but I did add a few new ones for nxos_vlan, for example, we now get back the list of VLANs that existed on the switch before and after the module was run, so now you can do a length check on the lists or ensure the new VLAN is in the list.

* If the module has a key called `new` or `final` in the results being returned, change this key to be called `end_state`


# COMMANDS


```python

    end_state = existing

    cmds = nested_command_list_to_string(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_switchport(device, interface, module)
```


Few things to point out here:
  1. Don't have `cmds = ''` before generating the command string.
    In the current modules, we have something like this:

    cmds = ''
    if commands:
        cmds = ' '.join(nxapi_lib.cmd_list_to_string(each)
                        for each in commands if each)

There are two functions to call now:  either  `nested_command_list_to_string` or `command_list_to_string` based on if the module has a list of commands or a list that includes lists of commands.

# END_STATE


```python

    end_state = existing

    cmds = nested_command_list_to_string(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            device.config(cmds)
            end_state = get_switchport(device, interface, module)
```


Ensure `end_state = existing` before the cmds are being generated and `end_state` only makes an API call if there was a change.  I state this because in some modules, there is this:

```
    results['proposed'] = proposed
    results['existing'] = existing
    results['new'] = nxapi_lib.get_portchannel(device, group)
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed
```


Going forward, it would look like this (removing the extra API call when there is no change)

```
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['commands'] = cmds
    results['changed'] = changed
```


Now for the fun stuff :)

We have two options as we migrate off of pycsco.  Copy and paste the code into the module only, or copy/paste and clean up where appropriate.

I suggest having a good balance.

Few things to note...

# COMMON FUNCTIONS FOR ALL (ALMOST ALL) MODULES

```python

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

```

The functions in the above code block should exist in almost every module.  If you feel you need to make a change to one of them, do it, but then do it to every other module with a `.py` extension :).  Not optimal, but this is what the plan is for now.

There may also be shared functions between modules.

For example, the next function exists in switchport and vlan modules:

```python
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

```

So just make sure if you make a change to it, you change it everywhere needed, and run any associated test playbook to make sure something didn't break.


# KEY MAPS and VALUE MAPS 

They should now be used to simplify changing to the keys/values we want to use.

For example, this was the get_vlan function before any change:

```python
def get_vlan(device, vid):
    """Retrieves attributes of a given VLAN based on a VLAN ID

    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        vid (str): The VLAN ID of which you want details for

    Returns:
        dictionary:
            if VLAN exists - k/v pairs include vlan_id, name,
                vlan_state
            else: returns empty dictionary

    """
    command = 'show vlan id ' + vid
    try:
        data = device.show(command)
    except CLIError:
        return {}
    data_dict = xmltodict.parse(data[1])
    vlan = {}

    try:
        vdata = data_dict['ins_api']['outputs']['output']['body'].get(
            'TABLE_vlanbriefid')['ROW_vlanbriefid']
        vlan['vlan_id'] = str(vdata['vlanshowbr-vlanid-utf'])
        vlan['name'] = str(vdata['vlanshowbr-vlanname'])
        vlan['vlan_state'] = str(vdata['vlanshowbr-vlanstate'])
        state = str(vdata['vlanshowbr-shutstate'])

        if state == 'shutdown':
            vlan['admin_state'] = 'down'
        elif state == 'noshutdown':
            vlan['admin_state'] = 'up'
    except (KeyError, AttributeError):
        return vlan

    return vlan
```


This is the new one:

```python
def get_vlan(device, vlanid, module):
    """Get instance of VLAN as a dictionary
    """

    command = 'show vlan id ' + vlanid

    body = parsed_data_from_device(device, command, module)

    if body:
        vlan_table = body['TABLE_vlanbriefid']['ROW_vlanbriefid']

        key_map = {
            "vlanshowbr-vlanid-utf": "vlan_id",
            "vlanshowbr-vlanname": "name",
            "vlanshowbr-vlanstate": "vlan_state",
            "vlanshowbr-shutstate": "admin_state"
        }

        vlan = apply_key_map(key_map, vlan_table)

        value_map = {
            "admin_state": {
                "shutdown": "down",
                "noshutdown": "up"
            }
        }

        vlan = apply_value_map(value_map, vlan)

    else:
        # VLAN DOES NOT EXIST
        return {}

    return vlan
```

You can see it's much cleaner - no long conditionals, etc.  

The key map is used to map from the keys/tags Cisco uses to the keys WE want to use.

Same goes for the value map, but is for values.  This one needs to be a dictionary of dictionaries.  NOTE: if you used a value map like this, you'll need a reverse value map when you generate the configs like this:

```python
def get_vlan_config_commands(vlan, vid):
    """Build command list required for VLAN configuration
    """

    reverse_value_map = {
        "admin_state": {
            "down": "shutdown",
            "up": "noshutdown"
        }
    }

    if vlan.get('admin_state'):
        # do we need to apply the value map?
        # only if we are making a change to the admin state
        # would need to be a loop or more in depth check if
        # value map has more than 1 key
        vlan = apply_value_map(reverse_value_map, vlan)

    VLAN_ARGS = {
        'name': 'name {name}',
        'vlan_state': 'state {vlan_state}',
        'admin_state': '{admin_state}',
        'mode': 'mode {mode}'
    }

    commands = []

    for param, value in vlan.iteritems():
        command = VLAN_ARGS.get(param).format(**vlan)
        if command:
            commands.append(command)

    commands.insert(0, 'vlan ' + vid)
    commands.append('exit')

    return commands
```

# PARSED_DATA_FROM_DEVICE FUNCTION

You can also see the new code has this:

```python
    command = 'show vlan id ' + vlanid

    body = parsed_data_from_device(device, command, module)

    if body:
        vlan_table = body['TABLE_vlanbriefid']['ROW_vlanbriefid']
```

This is how all new commands should be sent to the device.  Now the exception handling happens in ONE place for show commands.

Note: we need a conditional `if body` for vlan, because the body is null if the vlan doesn't exist. So, technically, you may not need the conditional for some modules.

And this another example:

```python
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

```


# STATE PARAMETER

State=absent on a few modules is not intuitive. If you feel we should change the function of the module, that is more than OKAY, let's just review it before you spend hours on the changes :)


# !!!!!!!!!!!!   MOST IMPORTANTLY !!!!!!!!!!!!!!

Create a test playbook for every module you re-factor:

Examples:

[https://github.com/jedelman8/nxos-ansible/blob/modules-no-pycsco-utils/test-playbooks/test-nxos_switchport.yml](https://github.com/jedelman8/nxos-ansible/blob/modules-no-pycsco-utils/test-playbooks/test-nxos_switchport.yml)

[https://github.com/jedelman8/nxos-ansible/blob/modules-no-pycsco-utils/test-playbooks/test-nxos_vlan.yml](https://github.com/jedelman8/nxos-ansible/blob/modules-no-pycsco-utils/test-playbooks/test-nxos_vlan.yml)


There are existing test playbooks for about half of the modules, feel free to use them as a baseline, but other than switchport/vlan, I know we should be changing what happens when state=absent, so definitely (and I mean definitely) take time to use the existing module as-is and point out what doesn't seem natural when making changes to the box.
