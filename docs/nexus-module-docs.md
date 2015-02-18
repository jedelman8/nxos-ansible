# Cisco NX-OS Ansible Module Docs
### *Network Automation with Cisco and Ansible*

---
### Requirements
* pycsco v0.1.4
* Nexus 9000
* NX-OS 6.1(2)I3(1)
* Testing performed on 9396 switches

---
### Modules

  * [nxos_get_interface - gets details stats on a particular interface](#nxos_get_interface)
  * [nxos_switchport - manages layer 2 switchport interfaces](#nxos_switchport)
  * [nxos_vrf_interface - manages interface specific vrf configuration](#nxos_vrf_interface)
  * [nxos_dir - manage dirs and files in the nx-os filesystem](#nxos_dir)
  * [nxos_vpc_interface - manages interface vpc configuration](#nxos_vpc_interface)
  * [nxos_ping - tests reachability using ping from nexus switch](#nxos_ping)
  * [nxos_vrf - manages global vrf configuration](#nxos_vrf)
  * [nxos_save_config - saves running configuration](#nxos_save_config)
  * [nxos_udld - manages udld global configuration params](#nxos_udld)
  * [nxos_mtu - manages mtu settings on nexus switch](#nxos_mtu)
  * [nxos_ipv4_interface - manages l3 attributes for ipv4 interfaces](#nxos_ipv4_interface)
  * [nxos_vpc - manages global vpc configuration](#nxos_vpc)
  * [nxos_copy - copy file from remote server to nexus switch](#nxos_copy)
  * [nxos_interface - manages physical attributes of interfaces](#nxos_interface)
  * [nxos_vlan - manages vlan resources and attributes](#nxos_vlan)
  * [nxos_portchannel - manages port-channel interfaces](#nxos_portchannel)
  * [nxos_command - send raw commands to cisco nx-api enabled devices](#nxos_command)
  * [nxos_hsrp - manages hsrp configuration on nx-api enabled devices](#nxos_hsrp)
  * [nxos_udld_interface - manages udld interface configuration params](#nxos_udld_interface)
  * [nxos_feature - manage features in nx-api enabled devices](#nxos_feature)
  * [nxos_get_facts - gets facts about nexus nx-api enabled switch](#nxos_get_facts)
  * [nxos_get_neighbors - gets neighbor detail from a nx-api enabled switch](#nxos_get_neighbors)

---

## nxos_get_interface
Gets details stats on a particular interface

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Gets details stats on a particular interface

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| interface  |   yes  |  | <ul></ul> |  Full name of interface, i.e. Ethernet1/1  |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |

#### Examples
```
# retrieve details info and stats on an interface (from 'show interface')
- nxos_get_interface: interface=Ethernet1/1 host={{ inventory_hostname }}


```

#### Notes
- Equivalent to using 'show interface $INTERFACEX/Y'

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_switchport
Manages Layer 2 switchport interfaces

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages Layer 2 interfaces

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| native_vlan  |   no  |  | <ul></ul> |  if mode=trunk, used as the trunk native vlan id  |
| access_vlan  |   no  |  | <ul></ul> |  if mode=access, used as the access vlan id  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manage the state of the resource  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| trunk_vlans  |   no  |  | <ul></ul> |  if mode=trunk, used as the vlan range to carry over trunk  |
| mode  |   yes  |  | <ul> <li>access</li>  <li>trunk</li> </ul> |  Mode for the Layer 2 port  |
| interface  |   yes  |  | <ul></ul> |  Full name of the interface, i.e. Ethernet1/1  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Config a switchport to be a trunk interface with native vlan 10 and carriers vlan 2-100
- nxos_switchport: interface=Ethernet1/1 mode=trunk native_vlan=10 trunk_vlans=2-100 host={{ inventory_hostname }}

# Config a switchport to an access port on vlan 20
- nxos_switchport: interface=Ethernet1/2 mode=access access_vlan=20 host={{ inventory_hostname }}

# Remove existing access port vlan configuration on a switchport (mode is required)
- nxos_switchport: interface=Ethernet1/2 host={{ inventory_hostname }} mode=access state=absent

# Remove existing trunk port vlan configuration on a switchport (mode is required)
- nxos_switchport: interface=Ethernet1/1 host={{ inventory_hostname }} mode=trunk state=absent

```

#### Notes
- When state=absent, if the switchport does not have a default config, it is set back to a default config from a vlan configuration perspective. This means, if state=absent, the resulting interface config will be an access port with vlan 1 configured as an access vlan even if the existing config is a trunk port.

- Access and Native VLANs are required to exist on the switch before configuring them with this module

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_vrf_interface
Manages interface specific VRF configuration

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages interface specific VRF configuration

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manages desired state of the resource  |
| vrf  |   yes  |  | <ul></ul> |  Name of VRF to be managed  |
| interface  |   yes  |  | <ul></ul> |  Full name of interface to be managed, i.e. Ethernet1/1  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# ensure vrf yankees exists on Eth1/1
- nxos_vrf_interface: vrf=yankees interface=Ethernet1/1 host={{ inventory_hostname }} state=present

# ensure yankees VRF does not exist on Eth1/1
- nxos_vrf_interface: vrf=yankees interface=Ethernet1/1 host={{ inventory_hostname }} state=absent

```

#### Notes
- Remove a VRF from an interface will still remove all L3 attributes just as it does from CLI

- VRF is not read from an interface until IP address is configured on that interface

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_dir
Manage dirs and files in the NX-OS filesystem

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Offers ability to create and delete directories and files on a Nexus switch

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Desired state of the resource / path  |
| path  |   yes  |  | <ul></ul> |  Path (with filename if deleting file)  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Ensure directory is created on target device
- nxos_dir: path='bootflash:new_config_dir' host={{ inventory_hostname }} state=present

# Ensure directory is not on target device
- nxos_dir: path='bootflash:new_config_dir' host={{ inventory_hostname }} state=absent

# Ensure file is not on target device
- nxos_dir: path='bootflash:switch_config1.cfg' host={{ inventory_hostname }} state=absent


```

#### Notes
- state=present should not be used when path is a file

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_vpc_interface
Manages interface VPC configuration

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages interface VPC configuration

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| portchannel  |   yes  |  | <ul></ul> |  group number of the portchannel that will be configured  |
| peer_link  |   no  |  | <ul></ul> |  Set to true/false for peer link config on assoicated portchannel  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manages desired state of the resource  |
| vpc  |   no  |  | <ul></ul> |  vpc group/id that will be configured on associated portchannel  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# config portchannel10 to be the peerlink
#- nxos_vpc_interface: portchannel=10 peer_link=true host={{ inventory_hostname }}

# config portchannel20 to be vpc20
#- nxos_vpc_interface: portchannel=20 vpc=20 host={{ inventory_hostname }}

# remove whatever VPC config is on portchannel if any exists (vpc xx or vpc peer-link)
- nxos_vpc_interface: portchannel=80 host={{ inventory_hostname }} state=absent

```

#### Notes
- Either vpc or peer_link param is required, but not both.

- State=absent removes whatever VPC config is on a port-channel if one exists.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_ping
Tests reachability using ping from Nexus switch

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Tests reachability using ping from switch to a remote destination

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| count  |   no  |  | <ul></ul> |  Number of packets to send  |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| dest  |   yes  |  | <ul></ul> |  IP address or hostname (resolvable by switch) of remote node  |
| source  |   no  |  | <ul></ul> |  Source IP Address  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| vrf  |   no  |  | <ul></ul> |  Outgoing VRF  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# test reachability to 8.8.8.8 using mgmt vrf
- nxos_ping: dest=8.8.8.8 vrf=management host={{ inventory_hostname }}

# Test reachability to a few different public IPs using mgmt vrf
- nxos_ping: dest={{ item }} vrf=management host={{ inventory_hostname }}
  with_items:
    - 8.8.8.8
    - 4.4.4.4
    - 198.6.1.4


```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_vrf
Manages global VRF configuration

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages global VRF configuration

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| description  |   no  |  | <ul></ul> |  Description of the VRF  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manages desired state of the resource  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| admin_state  |   no  |  | <ul> <li>up</li>  <li>down</li> </ul> |  Administrative state of the VRF  |
| vrf  |   yes  |  | <ul></ul> |  Name of VRF to be managed  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# ensure yankees VRF exists on switch
- nxos_vrf: vrf=yankees host={{ inventory_hostname }}

# ensure yankees VRF does not exist on switch
- nxos_vrf: vrf=yankees host={{ inventory_hostname }} state=absent

```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_save_config
Saves running configuration

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Saves running config to startup-config or file of your choice

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| path  |   no  |  | <ul></ul> |  {u'Path of destination.  Ex': u'bootflash:config.cfg, etc.'}  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |

#### Examples
```
# save running config to startup-config
- nxos_save_config: host={{ inventory_hostname }}

# save running config to dir in bootflash
- nxos_save_config: path='bootflash:configs/my_config.cfg' host={{ inventory_hostname }}


```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_udld
Manages UDLD global configuration params

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages UDLD global configuration params

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| reset  |   no  |  | <ul> <li>true</li>  <li>false</li> </ul> |  Ability to reset UDLD down interfaces  |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manage the state of the resource  |
| msg_time  |   no  |  | <ul></ul> |  Message time in seconds for UDLD packets  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| aggressive  |   no  |  | <ul> <li>enabled</li>  <li>disabled</li> </ul> |  Toggles aggressive mode  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# ensure udld aggressive mode is globally disabled and se global message interval is 20
- nxos_udld: aggressive=disabled msg_time=20 host={{ inventory_hostname }}

# Ensure agg mode is globally enabled and msg time is 15
- nxos_udld: aggressive=enabled msg_time=15 host={{ inventory_hostname }} state=present

# Ensure msg_time is unconfigured (if it is already 25- basically defaults back to 15 anyway)


```

#### Notes
- When state=absent, it unconfigures existing setings if they already exist on the switch.  It is cleaner to use state=present.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_mtu
Manages MTU settings on Nexus switch

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages MTU settings on Nexus switch

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| sysmtu  |   no  |  | <ul></ul> |  System jumbo MTU  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| mtu  |   no  |  | <ul></ul> |  MTU for a specific interface  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Specify desired state of the resource  |
| interface  |   yes  |  | <ul></ul> |  Full name of interface, i.e. Ethernet1/1  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Ensure system mtu is 9126
- nxos_mtu: sysmtu=9216 host={{ inventory_hostname }}

# Config mtu on Eth1/1 (routed interface)
- nxos_mtu: interface=Ethernet1/1 mtu=1600 host={{ inventory_hostname }}

# Config mtu on Eth1/3 (switched interface)
- nxos_mtu: interface=Ethernet1/3 mtu=9216 host={{ inventory_hostname }}

# Unconfigure mtu on a given interface
- nxos_mtu: interface=Ethernet1/3 mtu=9216 host={{ inventory_hostname }} state=absent


```

#### Notes
- Either sysmtu param is required or interface AND mtu params are req'd

- Absent unconfigures a given MTU if that value is currently present

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_ipv4_interface
Manages L3 attributes for IPv4 interfaces

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages Layer 3 attributes for IPv4 interfaces

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| ip_addr  |   yes  |  | <ul></ul> |  IPv4 IP Address  |
| mask  |   yes  |  | <ul></ul> |  Subnet mask for IPv4 IP Address  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Specify desired state of the resource  |
| interface  |   yes  |  | <ul></ul> |  Full name of interface, i.e. Ethernet1/1, vlan10  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Ensure Eth1/1 has an IP address of 10.1.100.2/24
- nxos_ipv4_interface: interface=Ethernet1/1 ip_addr=10.1.100.2 mask=24 host={{ inventory_hostname }} state=absent

# Ensure vlan10 has an IP address of 100.1.1.3/24
- nxos_ipv4_interface: interface=vlan10 ip_addr=10.1.100.3 mask=22 host={{ inventory_hostname }}

# Ensure vlan10 does not have an IP address
- nxos_ipv4_interface: interface=vlan10 host={{ inventory_hostname }} state=absent


```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_vpc
Manages global VPC configuration

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages global VPC configuration

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| domain  |   yes  |  | <ul></ul> |  VPC domain  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| system_priority  |   no  |  | <ul></ul> |  System priority device.  Remember they must match between peers.  |
| role_priority  |   no  |  | <ul></ul> |  Role priority for device. Remember lower is better.  |
| auto_recovery  |   no  |  | <ul> <li>true</li>  <li>false</li> </ul> |  Enables/Disables auto recovery  |
| pkl_vrf  |   no  |  | <ul></ul> |  VRF used for peer keepalive link  |
| delay_restore  |   no  |  | <ul></ul> |  manages delay restore command and config value in seconds  |
| peer_gw  |   no  |  | <ul> <li>true</li>  <li>false</li> </ul> |  Enables/Disables peer gateway  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manages desired state of the resource  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| pkl_dest  |   no  |  | <ul></ul> |  Destination (remote) IP address used for peer keepalive link  |
| pkl_src  |   no  |  | <ul></ul> |  Source IP address used for peer keepalive link  |

#### Examples
```
# ensure vpc domain 100 is configured
- nxos_vpc: domain=100 role_priority=1000 system_priority=2000 pkl_src=192.168.100.1 pkl_dest=192.168.100.2 host={{ inventory_hostname }}

# ensure peer gateway is enabled for vpc domain 100
- nxos_vpc: domain=100 peer_gw=true host={{ inventory_hostname }}

# ensure vpc domain does not exist on switch
- nxos_vpc: domain=100 host={{ inventory_hostname }} state=absent

```

#### Notes
- Although source IP isn't required on the command line it is required when using this module.  The PKL VRF must also be configured prior to using this module.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_copy
Copy file from remote server to Nexus switch

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Commands executed locally on the switch to copy a file from a remote server to a particular path/dir on the Nexus switch

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| server_path  |   yes  |  | <ul></ul> |  Absolute path including file name  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| server_pw  |   yes  |  | <ul></ul> |  Password used to login to the server from the switch  |
| server_un  |   yes  |  | <ul></ul> |  Username used to login to the server from the switch  |
| server_host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by switch) of the remote server that has currently has the file needed  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| local_path  |   yes  |  | <ul></ul> |  Path on the switch where the file should be stored upon transfer  |
| vrf  |   no  |  | <ul></ul> |  VRF used to source communication to the remote file server  |
| copy_type  |   no  |  | <ul> <li>scp</li> </ul> |  Protocol used to copy file from remote server to switch  |

#### Examples
```
# copy config file from server to switch
- nxos_copy:
    server_host=192.168.200.56
    server_path='/home/cisco/Public/switch_config.cfg'
    server_un=cisco
    server_pw=cisco
    copy_type=scp
    local_path='bootflash:switch_config.cfg'
    vrf=management
    host={{ inventory_hostname }}


```

#### Notes
- This module was tested with a remote Ubuntu 14.04 machine using SCP.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_interface
Manages physical attributes of interfaces

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages physical attributes on interface of NX-API enabled devices

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| description  |   no  |  | <ul></ul> |  Interface description  |
| duplex  |   no  |  | <ul></ul> |  Manage duplex settings on an interface  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li>  <li>default</li> </ul> |  Specify desired state of the resource  |
| admin_state  |   no  |  | <ul> <li>up</li>  <li>down</li> </ul> |  Administrative state of the interface  |
| mode  |   no  |  | <ul> <li>layer2</li>  <li>layer3</li> </ul> |  Manage Layer 2 or Layer 3 state of the interface  |
| interface  |   yes  |  | <ul></ul> |  Full name of interface, i.e. Ethernet1/1, port-channel10. Also supports non-idempotent keywords including all, ethernet, loopback, svi, portchannel  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| speed  |   no  |  | <ul></ul> |  Manage speed settings on an interface  |

#### Examples
```
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


```

#### Notes
- When using one of the five special keywords for the interface param, the module is not non-idempotent.  Keywords include all, ethernet, loopback, svi, and portchannel.

- This module is also used to create logical interfaces such as svis and loopbacks.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_vlan
Manages VLAN resources and attributes

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages VLAN configurations on NX-API enabled switches

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| vlan_state  |   no  |  | <ul> <li>active</li>  <li>suspend</li> </ul> |  Manage the vlan oper state of the VLAN (equiv to state {active | suspend} command  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| name  |   no  |  | <ul></ul> |  name of VLAN (not supported when using range of VLANs)  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manage the state of the resource  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| admin_state  |   no  |  | <ul> <li>up</li>  <li>down</li> </ul> |  Manage the vlan admin state of the VLAN (equiv to shut/no shut in vlan config mode  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| vlan_id  |   yes  |  | <ul></ul> |  vlan id or range of VLANs  |

#### Examples
```
# Ensure VLAN 50 exists with the name WEB and is in the shutdown state
 - nxos_vlan: vlan_id=50 host={{ inventory_hostname }} admin_state=down name=WEB

# Ensure VLAN is NOT on the device
- nxos_vlan: vlan_id=50 host={{ inventory_hostname }} state=absent

# Ensure a range of VLANs are present on the switch
- nxos_vlan: vlan_id="2-10,20,50,55-60" host={{ inventory_hostname }} state=present

# Ensure a group of VLANs are present with the given names
- nxos_vlan: vlan_id={{ item.vlan_id }} name={{ item.name }} host={{ inventory_hostname }} state=present
  with_items:
    - vlan_id: 10
      name: web
    - vlan_id: 20
      name: app
    - { vlan_id: 30, name: db }
    - vlan_id: 40
      name: misc
    - vlan_id: 99
      name: native_vlan

```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_portchannel
Manages port-channel interfaces

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages port-channel specific configuration parameters

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| group  |   yes  |  | <ul></ul> |  channel-group number for the port-channel  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manage the state of the resource  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| mode  |   no  |  | <ul> <li>active</li>  <li>passive</li>  <li>on</li> </ul> |  Mode for the port-channel, i.e. on, active, passive  |
| members  |   no  |  | <ul></ul> |  List of interfaces that will be managed in a given portchannel  |
| min_links  |   no  |  | <ul></ul> |  min links required to keep portchannel up  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Ensure port-channel 99 doesn't exist on the switch
- nxos_portchannel: group=99 host={{ inventory_hostname }} state=absent

# Ensure port-channel99 is created, add two members, and set to mode on
- nxos_portchannel:
    group: 99
    members: ['Ethernet1/1','Ethernet1/2']
    mode: 'active'
    host: "{{ inventory_hostname }}"
    state: present


```

#### Notes
- Absent removes the portchannel config and interface if it already exists

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_command
Send raw commands to Cisco NX-API enabled devices

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Raw show and config commands can be sent to NX-API enabled devices. For show commands there is the ability to return structured or raw text data. The command param when type=config can be a list or string with commands separated by a comma.

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| text  |   no  |  | <ul> <li>True</li>  <li>False</li> </ul> |  Dictates how data will be returned for show commands. Set to true if NX-API doesn't support structured output for a given command  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| command  |   yes  |  | <ul></ul> |  Show command as a string or a string of config commands separated by a comma or a list of config commands (complex args in Ansible)  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| type  |   yes  |  | <ul> <li>show</li>  <li>config</li> </ul> |  Represents the type of command being sent to the device  |

#### Examples
```
# Get CLI raw text output for a given command
- nxos_command: command='show run interface mgmt0 | inc description' host={{ inventory_hostname }} text=true type=show

# Get structured JSON data for given command
- nxos_command: command='show interface Ethernet1/1' host={{ inventory_hostname }} type=show

# Configure secondary interface on Eth1/2 with command as string
- nxos_command: command='interface Eth1/2,ip address 5.5.5.5/24 secondary' host={{ inventory_hostname }} type=config

# Configure secondary interface on Eth1/2 with command as list
- nxos_command:
    host: "{{ inventory_hostname }}"
    type: config
    command: ['interface Eth1/2','ip address 5.3.3.5/24 secondary']

```

#### Notes
- Only a single show command can be sent per task while multiple config commands can be sent.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_hsrp
Manages HSRP configuration on NX-API enabled devices

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages HSRP configuration on NX-API enabled devices

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| auth_type  |   no  |  | <ul> <li>text</li>  <li>md5</li> </ul> |  Authentication type  |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| group  |   yes  |  | <ul></ul> |  hsrp group number  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Specify desired state of the resource  |
| auth_string  |   no  |  | <ul></ul> |  Authentication string  |
| vip  |   yes  |  | <ul></ul> |  hsrp virtual IP address  |
| priority  |   no  |  | <ul></ul> |  hsrp priority  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| version  |   no  |  | <ul> <li>1</li>  <li>2</li> </ul> |  nxos_hsrp version  |
| interface  |   yes  |  | <ul></ul> |  Full name of interface that is being managed for HSRP  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# ensure hsrp is configured with following params on a SVI
- nxos_hsrp: group=10 vip=10.1.1.1 priority=150 interface=vlan10 preempt=enabled host={{ inventory_hostname }}

# ensure hsrp is configured with following params on a SVI
- nxos_hsrp: group=10 vip=10.1.1.1 priority=150 interface=vlan10 preempt=enabled host={{ inventory_hostname }} auth_type=text auth_string=CISCO

# removing hsrp config for given interface, group, and vip
- nxos_hsrp: group=10 interface=vlan10 vip=10.1.1.1 host={{ inventory_hostname }} state=absent


```

#### Notes
- Even when md5 is selected, only UNENCRYPTED key strings are supported in this release

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_udld_interface
Manages UDLD interface configuration params

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Manages UDLD interface configuration params

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| state  |   yes  |  | <ul> <li>present</li>  <li>absent</li> </ul> |  Manage the state of the resource  |
| mode  |   no  |  | <ul> <li>enabled</li>  <li>disabled</li>  <li>aggressive</li> </ul> |  Manages udld mode for an interface  |
| interface  |   no  |  | <ul></ul> |  FULL name of the interface, i.e. Ethernet1/1  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# ensure Ethernet1/1 is configured to be in aggressive mode
- nxos_udld_interface: interface=Ethernet1/1 mode=aggressive state=present host={{ inventory_hostname }}

# Remove the aggressive config only if it's currently in aggressive mode and then disable udld (switch default)
- nxos_udld_interface: interface=Ethernet1/1 mode=aggressive state=absent host={{ inventory_hostname }}

# ensure Ethernet1/1 has aggressive mode enabled
- nxos_udld_interface: interface=Ethernet1/1 mode=enabled host={{ inventory_hostname }}

# ensure Ethernet1/1 has aggressive mode disabled


```

#### Notes
- When state=absent, it unconfigures existing setings if they already exist on the switch.  It is much cleaner to use state=present for all options.

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_feature
Manage features in NX-API enabled devices

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Offers ability to enable and disable features in NX-OS

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| state  |   yes  |  | <ul> <li>enabled</li>  <li>disabled</li> </ul> |  Desired state of the feature  |
| feature  |   yes  |  | <ul></ul> |  Name of feature  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |

#### Examples
```
# Ensure lacp is enabled
- nxos_feature: feature=lacp state=enabled host={{ inventory_hostname }}

# Ensure ospf is disabled
- nxos_feature: feature=ospf state=disabled host={{ inventory_hostname }}

# Ensure vpc is enabled
- nxos_feature: feature=vpc state=enabled host={{ inventory_hostname }}


```

#### Notes
- feature name must match that from the CLI

- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_get_facts
Gets facts about Nexus NX-API enabled switch

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Offers ability to extract facts from device

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| protocol  |   no  |  | <ul> <li>http</li> </ul> |  Dictates connection protocol to use for NX-API  |
| detail  |   no  |  | <ul> <li>true</li>  <li>false</li> </ul> |  if set to true, returns detailed statistics for interfaces equivalent to 'show interface status'  |

#### Examples
```
# retrieve facts
- nxos_get_facts: host={{ inventory_hostname }}

# retrieve facts with detailed info for interfaces (from 'show interface status')
- nxos_get_facts: host={{ inventory_hostname }} detail=true


```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


## nxos_get_neighbors
Gets neighbor detail from a NX-API enabled switch

  * Synopsis
  * Options
  * Examples

#### Synopsis
 Gets CDP or LLDP information from the switch

#### Options

| Parameter     | required    | default  | choices    | comments |
| ------------- |-------------| ---------|----------- |--------- |
| username  |   no  |  | <ul></ul> |  Username used to login to the switch  |
| protocol  |   yes  |  | <ul> <li>http</li>  <li>https</li> </ul> |  Dictates connection protocol to use for NX-API  |
| host  |   yes  |  | <ul></ul> |  IP Address or hostname (resolvable by Ansible control host) of the target NX-API enabled switch  |
| password  |   no  |  | <ul></ul> |  Password used to login to the switch  |
| type  |   yes  |  | <ul> <li>cdp</li>  <li>lldp</li> </ul> |  Specify neighbor protocol on how information should be gathered from switch  |

#### Examples
```
# retrieve cdp neighbors
- nxos_get_neighbors: type=cdp host={{ inventory_hostname }}

# retrieve lldp neighbors
- nxos_get_neighbors: type=lldp host={{ inventory_hostname }}

```

#### Notes
- While username and password are not required params, they are if you are not using the .netauth file.  .netauth file is recommended as it will clean up the each task in the playbook by not requiring the username and password params for every tasks.

- Using the username and password params will override the .netauth file


---


---
Created by Jason Edelman. February 2015.
