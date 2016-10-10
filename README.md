# UPDATE 10/10/16

The modules in this repo are officially deprecated.  Going forward, you should use all modules that are in Ansible [core](https://github.com/ansible/ansible-modules-core/tree/devel/network/nxos) - all of them have been migrated such that when you install Ansible 2.2, you get the modules automatically!

This `README.md` can still be used for guidance.

### Network Automation with Ansible and Cisco Nexus Switches


#### Want to get an overview of the modules right away?  Check out the docs [here](docs/nexus-module-docs.md)

## Table of Contents
  
  * [Introduction](#introduction)
  * [What is Ansible?](#what-is-ansible)
  * [What is Nexus NX-API?](#what-is-nexus-nx-api)
  * [Environment Setup](#environment-setup)
    * [Option 1 - Manual Install](#option-1---manual-install)
    * [Option 2 - Get Your Docker On](#option-2---get-your-docker-on)
  * [Prepare Your Cisco Nexus Switches](#prepare-your-cisco-nexus-switches)
  * [Getting Familiar with Ansible](#getting-familiar-with-ansible)
    * [Example Playbook](#example-playbook)
    * [Hosts File](#hosts-file)
    * [Executing Ansible Playbooks](#executing-ansible-playbooks)
  * [Network Configuration Templating](#network-configuration-templating)
    * [Creating the Configs Directory](#creating-the-configs-directory)
    * [Creating a Template](#creating-a-template)
    * [Intro to Ansible Variables](#intro-to-ansible-variables)
    * [Creating a New Playbook](#creating-a-new-playbook)
    * [Dynamically Creating Config Files](#dynamically-creating-config-files)
  * [Automated Configuration Management](#automated-configuration-management)
  * [Automated Data Collection](#automated-data-collection)
  * [Example Playbooks](#example-playbooks)
  * [Cisco NX-OS Module Docs](#cisco-nx-os-module-docs)
  * [Requirements](#requirements)
  * [Contributions](#contributions)
  * [License](#license)
  * [Appendix - Features to Know](#appendix---features-to-know)
    * [ansible-doc](#ansible-doc)
    * [Verbose Output](#verbose-output)
    * [Dry Run Check Mode](#Dry-Run-check-mode)


# Introduction
With the Cisco Nexus series switches, Cisco offers two modes of operation: Application Centric Infrastructure (ACI) mode and standalone mode.  In the ACI mode of operation, Cisco Nexus 9000 hardware can be deployed along with the Application Policy Infrastructure Controller (APIC) to deploy and manage the network as a single system.  Since not all Nexus installs may result in an ACI deployment, Cisco offers other types of programmability and automation options for when Nexus switches are deployed in standalone mode.  These include Python on-box, the support for on-box Linux Containers (LXC) in which the user can install 3rd party automation packages, Puppet, Chef, and a device API (called NX-API).  

In addition to the existing options, there is now integration (found in this repo) with Ansible, another very popular DevOps automation tool.  Integration between Ansible and the Nexus platform occurs by using Ansible's open and extensible framework along with the NX-API found on a few different Nexus platforms (not just the N9K).  

# What is Ansible
Ansible is an open source IT configuration management and automation tool.  Similar to Puppet and Chef, Ansible has made a name for itself among system administrators that need to manage, automate, and orchestrate various types of server environments.  Unlike Puppet and Chef, Ansible is agentless, and does not require a software agent to be installed on the target node (server or switch) in order to automate the device.  By default, Ansible requires SSH and Python support on the target node, but Ansible can also be easily extended to use any API.  In the Ansible modules developed for NX-OS as part of this project, Ansible modules make API calls against the NX-API to gather real-time state data and to make configuration changes on Cisco Nexus devices.

For more on Ansible, please reference Ansible's [official docs](http://docs.ansible.com/).

# What is Nexus NX-API
NX-API is a REST-like API for NX-OS based systems.  NX-API allows network administrators and programmers to send CLI commands in an API call down to a network device eliminating the need for expect scripting since nearly all communication for NX-API uses structured data.  Admins can choose from JSON, XML, or JSON-RPC.

Support for NX-API is available on the Nexus 9000 and Nexus 3000 series switches with support coming soon for other Nexus series platforms.  In configuration mode on NX-OS platforms, perform the command `feature ?` to check and see if `nxapi` is listed as an available feature.  Consult the release notes to be sure a particular platform supports NX-API if you don't have a device to test on.

For more detail on NX-API, check the offical [docs](http://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/sw/6-x/programmability/guide/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide/b_Cisco_Nexus_9000_Series_NX-OS_Programmability_Guide_chapter_011.html).

# Environment Setup
The rest of this document will be used to describe and show how to automate Cisco Nexus environments using the Ansible open source IT automation framework.  It will cover high level installation procedures and examples of how to get started.

Before going through examples, we'll first walk through getting a basic Ansible environment setup that will specifically be used to automate Cisco data center networks that have NX-OS switches deployed.

* [Option 1 - Manual Install](#option-1---manual-install)
* [Option 2 - Get Your Docker On](#option-2---get-your-docker-on)

## Option 1 - Manual Install

* [Ansible Control Host](#ansible-control-host)
* [Cisco Dependencies](#cisco-dependencies)
* [Cisco NX-OS Ansible Modules](#cisco-nx-os-ansible-modules)

### Ansible Control Host
Ansible does not require a dedicated server to be used.  In fact, many machines could have Ansible installed and they can be used to simultaneuously automate any given environment (not recommending that here, but it's definitely a nice option to have). 

The setup that we are showing here will be using an Ubuntu machine from Cisco that is also called the all-in-one onePK Virtual Machine.  This VM can be downloaded from [Cisco's DevNet community site](https://developer.cisco.com/downloads/all-in-one-VM-1.3.0.181.ova).  It's worth noting the same steps would hold true for a fresh install of Ubuntu.  Testing has also worked on using Vagrant Ubuntu boxes.

If you wish to use your own Linux Operating System (including MAC OS), you should follow the detailed [installation steps found on Ansible's website.](http://docs.ansible.com/intro_installation.html#getting-ansible)

This [YouTube video](https://www.youtube.com/watch?v=v9a_2-9hlus) goes through this process.

Assuming you now have a base Linux distribution up and running, perform the following steps:

**Step 1 - Update your system**
```
sudo apt-get update
```

**Step 2 - Ensure pip (Python package manager) is installed**

```
sudo apt-get install python-pip
```

**Step 3 - Install Ansible**
```
sudo pip install ansible
```

**Step 4 - Ensure SSH is installed** (not a requirement, but helpful and also required for the `nxos_copy` module)
```
sudo apt-get install openssh-server
```

**Step 5 - Update the /etc/hosts file**

Ensure you can ping your Nexus NX-API enabled switches by name (not required, but helpful).  Here is an example from the all-in-one onePK VM hosts file.  This shows the file after adding one new entry for `n9k1`.

```
cisco@onepk:~$ cat /etc/hosts
127.0.0.1 localhost
127.0.1.1 onepk
10.10.10.110    router1.3node.example.com
10.10.10.120    router2.3node.example.com
10.10.10.130    router3.3node.example.com
172.31.217.133  n9k1  # <<--- showing one Nexus 9000
```

To make the change to the hosts file as shown above, any number of text editors like vi, vim, gedit, Sublime Text, etc. can be used.  To install gedit, you can issue the following terminal command: `sudo apt-get install gedit` and once it's installed, you can open the hosts file by issuing the command `sudo gedit /etc/hosts`.  Same can be done with `vim`. From there, make the change and save the file.  Of course, you can also do this with your text editor of choice too.

You should now be able to `ping n9k1` to get a response back from the MANAGEMENT IP address of the Nexus switch.  In our case, that is 172.31.217.133.


**Step 6 - ONLY FOR VAGRANT USERS**

If you are using an Ubuntu box with Vagrant, also perform the following command:
```
$ sudo pip install markupsafe
```


### Cisco Dependencies
When you download and install Ansible, you get "batteries included" functionality for automating Linux environments.  You can do things like manage services, packages, files, etc., "out of the box" without any other required software.  However, Ansible "Core" does not offer the ability to manage and automate network devices. This functionality comes through custom integration (which is what we are showing here).

In order to begin automating Cisco Nexus switches with Ansible, a few dependencies are required before actually using Ansible modules that communicate with Cisco Nexus switches.  These dependencies include a Python library called `xmltodict` that converts xml objects to JSON, but also two Python modules (wrappers and helper functions) used to communicate with NX-API devices.  

All of these dependencies can be installed by issuing the following command:
```
cisco@onepk:~$ sudo pip install pycsco
```

### Cisco NX-OS Ansible Modules
In addition to installing the dependencies, you'll now need the actual Ansible modules that will be used to automate and manage Cisco Nexus NX-API enabled systems.  Instead of just focusing on the modules, we'll clone the entire repo (that includes the modules), and then move the modules to a location to allow Ansible's built-in documentation to work.

**Step 1: Ensure git is installed**

```
cisco@onepk:~$ sudo apt-get install git
```

**Step 2: Clone this repository**

```
cisco@onepk:~$ git clone https://github.com/jedelman8/nxos-ansible.git
```

**Step 3: Create Two New Directories**

```
cisco@onepk:~$ sudo mkdir -p /etc/ansible

cisco@onepk:~$ sudo mkdir -p /usr/share/ansible
```


**Step 4: Move  Modules and Config to New Directories**

```
cisco@onepk:~$ sudo mv nxos-ansible/files/ansible.cfg /etc/ansible/ansible.cfg

cisco@onepk:~$ sudo mv nxos-ansible/library/ /usr/share/ansible/cisco_nxos
```


> Note: these steps are being done for two reasons.  First, to ensure users can create multiple working directories such they don't always need a `library` directory local to their playbooks.  Second, to ensure the `ansible-doc` utility works for the Cisco modules.  This utility is covered below, but in short, it provides built-in docs for Ansible modules.
> 
> Note: the only change in the ansible.cfg file from the default is the setting of the flag `gathering = explicit`.  If you do not have this, you'll need to set `gather_facts: False` for each play.

**Step 5 - Move and Edit the Authentication File**

This is an optional step, but simplifies the Ansible playbooks by not needing to include a username and password for each task.

```
cisco@onepk:~$ sudo mv nxos-ansible/files/.netauth ~/.netauth
```

**Edit the file**
```
cisco@onepk:~$ sudo vim .netauth
```

Make changes using a text editor (example above is using vim) such that it follows the format below.  Your file MUST continue to look the one provided (*just insert the username and password for your switches*).


```
# the .netauth file
# make sure you input the proper creds for your device
---

cisco:
  nexus:
    username: "cisco"
    password: "cisco"

```


If the username and password differs for a switch or group of switches, you must then use the username and password parameters in the Ansible playbook for each task.  This can be seen in the **Automated Data Collection** playbook examples that be found below.

> Note: if you are using Ansible Tower, you'll need to disable a security setting to allow the use of .netauth to work, i.e. the reading in of values of a file that exists outside of your working directory.
> 
> Note: this section will be updated over time to include instructions for using `ansible-vault`.

## Option 2 - Get Your Docker On

**Step 1 - Download Docker Image**

Ansible does not require a dedicated server to be used.  In fact, many machines could have Ansible installed and they can be used to simultaneuously automate any given environment (not recommending that here, but it's definitely a nice option to have). 

> Note: This option assumes you already have Docker installed.  If you don't, follow the instructions that can be found [here](https://docs.docker.com/installation/).

The Docker image will come ready to go with Ansible along with the Cisco dependencies required to start automating Nexus environments.

This [YouTube video](https://www.youtube.com/watch?v=ftxBCCKbVn4) goes through this process.

```
sudo docker pull jedelman8/nxos-ansible
```

Make sure you see the new image
```
sudo docker images
```

Start your first container for automating networks!
```
sudo docker run -it jedelman8/nxos-ansible
```

**Step 2 - Update hosts File**

Ensure you can ping your Nexus NX-API enabled switches by name (not required, but helpful) from the new container.  Here is a sample from a test container.  This shows the file after adding two new entries for `n9k1` and `n9k2`.

```
root@3b5d22fa1231b:~$ cat /etc/hosts
172.17.0.23      3b5d22fa1231b
127.0.0.1        localhost

#### Add your Nexus Switches here
#### MUST Use the MGMT0 IP Address

10.1.10.100      n9k1
10.1.10.101      n9k2

```

`vim` is already installed in the container, so feel free to use it to modify the `hosts` file.

You should now be able to `ping n9k1` to get a response back from the MANAGEMENT IP address of the Nexus switch.


**Step 3 - Update Authentication File**

**Edit the file**
```
root@3b5d22fa1231b:~$ sudo vim .netauth
```

Make changes using a text editor (example above is using vim) such that it follows the format below.  Your file MUST continue to look the one provided (*just insert the username and password for your switches*).

```
# the .netauth file
# make sure you input the proper creds for your device
---

cisco:
  nexus:
    username: "cisco"
    password: "cisco"

```


If the username and password differs for a switch or group of switches, you must then use the username and password parameters in the Ansible playbook for each task.  This can be seen in the **Automated Data Collection** playbook examples that be found below.

> Note: if you are using Ansible Tower, you'll need to disable a security setting to allow the use of .netauth to work, i.e. the reading in of values of a file that exists outside of your working directory.
> 
> Note: this section will be updated over time to include instructions for using `ansible-vault`.


# Prepare Your Cisco Nexus Switches
At this point, Ansible, the Cisco dependencies, and the custom Cisco Ansible modules should be installed on the *Ansible control host*  if you've been following along.  The last step is to ensure the Nexus switches are configured correctly to work with Ansible.  This basically means to ensure two things: (1) make sure NX-API is enabled and (2) make sure the Ansible control host can ping the  mgmt0 interface of the switch(es).

The `feature` command is used to enable NX-API.  After it's enabled, ensure the device is listening on port 80.  The modules in this repo only operate using http/80.  Https/443 to come in the future.

```
n9k1# config t
Enter configuration commands, one per line.  End with CNTL/Z.
n9k1(config)# feature nxapi
n9k1(config)# exit

n9k1# show nxapi
nxapi enabled
Listen on port 80
Listen on port 443
```

For the mgmt0 interface and outbound connectivity, there are a few things that need to happen before using the modules.

1. Configure an IP address on mgmt0
2. Configure a default route for the management VRF (or at a minimum a route to the Ansible control host)
3. Test connectivity between the Ansible control host and mgmt0 (remember if you are using Virtualbox or Fusion with a NAT configuration, you won't be able to ping from your switch to your VM)

# Getting Familiar with Ansible
Ansible is an extremely robust IT automation framework, so to understand what it is fully capable of, please consult the official [Ansible docs](http://docs.ansible.com/).  We'll just be covering the basics to show how to get started.  First, you need to understand a few things about basic Ansible terminology that we'll review here.  

The terms that you must understand include playbooks, plays, tasks, and modules.  A playbook is a YAML file that has any number of plays in which each play can have one or more tasks in which you want to automate.  Each task "calls" an Ansible module which executes the code required to accomplish the given task.  Clear as mud?  We'll dive into these concepts using a few examples in the following sections.

* [Example Playbook](#example-playbook)
* [Hosts File](#hosts-file)
* [Executing Ansible Playbooks](#executing-ansible-playbooks)

### Example Playbook

A sample playbook is shown below.  Assume that this playbook is saved as `nexus-automation.yml` and is stored in your working directory - `nxos-ansible` --- the directory that was downloaded when you cloned the repo.  This will continuously be referred to as the current Ansible **working directory**.  Since this walk through is using the Cisco all-in-one onePK virtual machine, the full path to this file is: `/home/cisco/nxos-ansible/nexus-automation.yml`.  Feel free to create it and follow along.   

```
---

- name: sample playbook
  hosts: n9k1

  tasks:

    - name: default interfaces
      nxos_interface: interface={{ item }} state=default host={{ inventory_hostname }}
      with_items:
        - Ethernet1/1
        - Ethernet2/1

    # Ensure an interface is a Layer 3 port and that it has the proper description
    - name: config interface
      nxos_interface: interface=Ethernet1/1 description='Configured by Ansible' mode=layer3 host={{ inventory_hostname }}

    # Admin down an interface
    - nxos_interface: interface=Ethernet2/1 admin_state=down host={{ inventory_hostname }}

```


As you'll see above, the playbook is a set of automation instructions defined in YAML.  The `---` denotes the start of a YAML file, and in this case, also an Ansible playbook.  Just below, there is a grouping of two key-value pairs that will be used for the play that follows.  `name` is arbritary and is text that is displayed when the playbook is run. `hosts` denotes the host or group of hosts that will have the automation instructions, or tasks, executed against.  

**If you named your switch something other than `n9k1` in the `/etc/hosts/` file, use your switch name!**  The inventory (or hosts) file is also an important component of Ansible that will be covered in the next section.

Just below those two k-v pairs, there is a list of three tasks that will be automated.  They all call the `nxos_interface` module.  Following the module name are a number of key-value pairs in the form of key=value.  These k-v pairs are sent to the module for processing against the device.  

> Note: Nearly all Cisco modules are idempotent, which means, if the device is already in the desired state, no change will be made.  A change will only be made if it's required to get the device into the desired state.  

As you can probably tell, the first task will default Eth1/1 and Eth2/1, the second tasks will ensure Ethernet1/1 has the description defined in the k-v pair and also ensure that Ethernet1/1 is a layer 3 port.  The third task ensures that Ethernet2/1 is in the admin down state.  As stated previously, these modules are idempotent, so if Ethernet2/1 is already in the admin down state, no commands will be sent to the device (as an example).

### Hosts File

For each play, the administrator needs to define the host(s) that the set of tasks will be executed against.  The example above executes two tasks against `n9k1`.  This can be seen in the top left of the playbook where `hosts: n9k1` is defined.  This can be a group of hosts or a single host and maps directly back to an inventory, or hosts, file.

The inventory hosts file is an ini based file.  The hosts file for the above example looks like this:
```
[all:vars]
ansible_connection = local

[spine]
n9k1
n9k2

[leaf]
n3k1
n9k3
n9k4

[wan]
boston  mgmt_ip=10.1.10.1
nyc  mgmt_ip=10.1.20.1
sjc
rtp
richardson

```

>Note: You will need the `[all:vars]` section for every inventory file you create since we are using a custom connection protocol.  The other option is to use `connection: local` for each play.  If you are integrating with server environments, you may need a combination of both.

Since you cloned the repo, just make sure you are in the `nxos-ansible` and issue the command: 

`cisco@onepk:~/nxos-ansible$ cat hosts`

You should see what is shown in the text above.  If you are only testing with a single switch, you can remove all other 9k# hosts from the inventory file.  If you don't, you'll get errors below as you run through the examples.

> Note: You can disregard the `wan` section.  That'll be used in an upcoming example.

> Note: the names in the hosts file should match what you have in DNS, the `/etc/hosts/` file, or it can just be the mgmt IP Address of the switch.

The same play could have used `hosts: spine` instead of `hosts: n9k1` in order to automate n9k1, n9k2 for all tasks in a given play or `hosts: all` to automate all hosts.

> Note: you may have noticed `{{ inventory_hostname }}` in the playbook.  Double curly braces are used to reference variables and it's worth noting that `inventory_hostname` is an internal / built-in Ansible variable.  This variable is equivalent to the hostname as defined in the hosts file as the hosts get iterated through to execute the set of tasks in the playbook.  In this previous example, this means that `n9k1` would get sent to the Ansible module during the first task run, `n9k2` for the second run, and so on, etc.

> Note: names are not required for the modules.  IP Addresses work just fine too if DNS or the hosts file isn't defined.

### Executing Ansible Playbooks

By now, you should have a very high level understanding of the layout of an Ansible playbook. It's worth taking a look at how Ansible playbooks are executed.  As stated above, the filename of the playbook is `nexus-automation.yml`.  The name of the inventory hosts file is called `hosts`.  For this example, ensure both are stored in the same working directory (`/home/cisco/nxos-ansible/`).  As with most files being reviewed in this document, they will have already been created and downloaded when you cloned the repository, but they are still being covered for completeness.

To execute the playbook, the following terminal command is used:
```
cisco@onepk:~/nxos-ansible$ ansible-playbook -i hosts nexus-automation.yml
```

`-i hosts` tells the system which **i**nventory hosts file to use.

After running the playbook, feel free to check the changes out on your switch.

In order to not have to continuously state where the hosts file is, you can set the `ANSIBLE_HOSTS` environment variable.  Within your working directory, you can `source` the `env-setup` file.

```
cisco@onepk:~/nxos-ansible$ source env-setup                  
```

That covers some of the basics to get started with Ansible.  The next section walks through how to use an Ansible core module called `template` that can help in creating network device templates and simplify how configuration files are created for network devices of all types.  Following the templating section is when we'll cover using the Cisco specific Ansible modules.


#### Network Configuration Templating

* [Creating the Configs Directory](#creating-the-configs-directory)
* [Creating a Template](#creating-a-template)
* [Intro to Ansible Variables](#intro-to-ansible-variables)
* [Creating a New Playbook](#creating-a-new-playbook)
* [Dynamically Creating Config Files](#dynamically-creating-config-files)

The previous sections gave a high level overview of Ansible and reviewed an example playbook.  In this section, we'll look at how to use Ansible to template build configurations for network devices by walking through another playbook and learning a bit more about Ansible.

First, we'll ensure the inventory `hosts` file looks like the following.  You should have the group `wan` and each hostname and variable underneath as shown here:

```
[spine]
n9k1
n9k2

[leaf]
n9k3
n9k4

[wan]
boston  mgmt_ip=10.1.10.1
nyc  mgmt_ip=10.1.20.1
sjc
rtp
richardson

```

> This example will run through building IOS router configurations.  This is to show that **templating** with Ansible has no direct correlation to the Nexus or NX-OS platform.  Note: the only requirement for Nexus is when you are using the custom Cisco Ansible modules that'll be covered in the next section.

In this section, we'll be using the Ansible core module called `template` to automate the creation of the configuration files required for routers that exist at the 5 locations listed in the hosts file.  First, we'll do two things before creating the configurations. (1) create a new directory that will store the final configs and (2) Create a very basic config template.  Again, this will have already been done for you if you cloned the repository.  

### Creating the Configs Directory

This is straightforward.  A new directory will be created that will store the final config files rendered for each device in the hosts file.  We'll create a new directory called `configs` (`mkdir configs`) that exists in the working directory (`/home/cisco/nxos-ansible/configs`).

### Creating a Template

Ansible integrates natively with Jinja2 templates, so that's what will be used here.  Create a new file called routers.j2 in the working directory.

>Note: since this is already in your repository, feel free to open it up to view it.  You can issue a `cat templates/routers.j2` to check it out.

The contents should look like the following:
```
hostname {{ inventory_hostname }}

interface mgmt0
  ip address {{ mgmt_ip }}

ntp server {{ ntp_server }}
snmp-server {{ snmp_server }}

username cisco password cisco

```


>Note: this is an extremely basic config template.  It is possible to get much more robust with how templates are created using Ansible with different variables per site, region, etc.

For more details on Jinja2, please reference the official Jinja2 [docs](http://jinja.pocoo.org/docs/dev/).

As you may recall, `{{ inventory_hostname }} ` is an internal Ansible variable, so the hostname of each device, will be equivalent to what is defined in the hosts file.  

### Intro to Ansible Variables

The other variables found in the Jinja template can be defined in a number of locations.  For this example, we'll show defining them in three locations.  

> Note: for more detail about variables and variables scope, please reference the Ansible [variables docs](http://docs.ansible.com/playbooks_variables.html).

First, variables can be defined in the `hosts` file as you may have already noticed.

```
[spine]
n9k1
n9k2

[leaf]
n9k3
n9k4

[wan]
boston  mgmt_ip=10.1.10.1
nyc  mgmt_ip=10.1.20.1
sjc
rtp
richardson
```

Second is in a file called `wan.yml` that needs to be created and stored in a `group_vars` directory.  This group will match the group as defined in the `hosts` file.

The path to this file should be the ansible working directory `group_vars/wan.yml`, so for this complete example it would be `/home/cisco/nxos-ansible/group_vars/wan.yml`  Any variables found in `wan.yml` can be accessed by any device in the WAN group within the hosts file.

`wan.yml` looks like the following:

```
---
ntp_server: 192.168.100.11
snmp_server: 192.168.100.12
```

The third location we'll store variables is in host specific variables files.  Also within the working directory, there will be a new dir called `host_vars`.  The dir should contain as many files that are required that contain variables that can only be used for and by specific devices.  In this example, there will be three new yaml files that exist within the `host_vars` directory.  They are `sjc.yml`, `rtp.yml`, and `richardson.yml`.  These file names must match the name of the device as defined in the inventory hosts file.

> Variables can also be stored in the all.yml file that would exist in the group_vars directory.

These three files look like the following:

File: `/home/cisco/nxos-ansible/host_vars/sjc.yml`

```
---
mgmt_ip: 10.1.30.1
```

File: `/home/cisco/nxos-ansible/host_vars/rtp.yml`

```
---
mgmt_ip: 10.1.40.1
```

File: `/home/cisco/nxos-ansible/host_vars/richardson.yml`

```
---
mgmt_ip: 10.1.50.1
```

### Creating a New Playbook

In the working directory, create a new playbook called `config-builder.yml`. It should have the following contents:

```
---

- name: template building
  hosts: wan

  tasks:

    # Create config files
    - template: src=templates/routers.j2 dest=configs/{{ inventory_hostname }}.cfg
```

This playbook will leverage the newly created hosts file, all.yml, three different host variables files (<hostname>.yml), and the Jinja2 template.  

### Dynamically Creating Config Files

Putting this all together, we'll now be able to execute the playbook.
```
cisco@onepk:~/nxos-ansible$ ansible-playbook config-builder.yml

PLAY [template building] ****************************************************** 

TASK: [template src=templates/routers.j2 dest=configs/{{ inventory_hostname }}.cfg] ****** 
changed: [sjc]
changed: [rtp]
changed: [boston]
changed: [richardson]
changed: [nyc]

PLAY RECAP ******************************************************************** 
boston                     : ok=1    changed=1    unreachable=0    failed=0   
nyc                        : ok=1    changed=1    unreachable=0    failed=0   
richardson                 : ok=1    changed=1    unreachable=0    failed=0   
rtp                        : ok=1    changed=1    unreachable=0    failed=0   
sjc                        : ok=1    changed=1    unreachable=0    failed=0 
```

You can verify the config files were created by navigating to the `configs` directory and checking out the new config files.

```
cisco@onepk:~/nxos-ansible$ cd configs
cisco@onepk:~/nxos-ansible/configs$ 
cisco@onepk:~/nxos-ansible/configs$ cat sjc.cfg 

hostname sjc

interface mgmt0
  ip address 10.1.30.1

ntp server 192.168.100.11
snmp-server 192.168.100.12

username cisco password cisco

cisco@onepk:~/nxos-ansible/configs$ 
```

```
cisco@onepk:~/nxos-ansible/configs$ cat nyc.cfg 

hostname nyc

interface mgmt0
  ip address 10.1.20.1

ntp server 192.168.100.11
snmp-server 192.168.100.12

username cisco password cisco

```

As stated previously much more can be done to streamline the creation of network configuration files using Ansible.  If a small change needs to be made across devices, then it could be updated in the template or variables file, and the playbook can simply be executed again.  You can also explore creating different groups in the hosts file and having `<group_name>.yml` stored in the `group_vars` directory to streamline the creation for larger scale deployments that require different inputs per region, site, building, tenant, etc.

In the sections that follow, we'll take a look at using the Cisco specific Ansible modules that can be used for automated data collection and configuration management.


#### Automated Configuration Management

We'll now walk through a few example playbooks used for automating configuration management.  For the examples, it can be assumed that the `hosts` file being used has several Nexus 9000 series switches such as what is shown below. If you only have one, that's fine.  Just make sure `hosts` file reflects that.

**AND ALSO REMOVE THE `wan` GROUP**

```
[spine]
n9k1
n9k2

[leaf]
n9k3
n9k4
```


> The examples shown could be deployed in one large playbook, but they are being shown individually below in order to make them more digestable and easier to test.

If you are following along, you can build the playbooks yourself or move/copy them from the `example-playbooks` directory into the `nxos-ansible` directory.  The file name for each playbook can be seen below in the text on the first line of each playbook.  You can use the `mv` or `cp` commands to move the files accordingly.  To get them all at once, issue the following command:

```
cisco@onepk:~/nxos-ansible$ cp example-playbooks/how-to/readme-example*.yml .
```


And remember to execute each playbook, you use the following command:

```
cisco@onepk:~/nxos-ansible$ ansible-playbook <PLAYBOOKNAME.YML> -i hosts
```

Example 1: Wipe out up logical interfaces and shut down all Ethernet interfaces

> Since we are using `hosts: all` you will need to remove the `wan` group from the hosts file.  Otherwise, just change the groups you are automating!
> Ensure you have connectivity to all Nexus switches within the `hosts` file.  It's fine if you are just using one.

Playbook:
```
# example-playbooks/readme-example1.yml
---

- name: example 1 - baseline
  hosts: all

  tasks:
    - name: ensure no logical interfaces exist on the switch
      nxos_interface: interface={{ item }} state=absent host={{ inventory_hostname }}
      with_items:
        - loopback
        - portchannel
        - svi

    - name: ensure all Ethernet ports are admin down
      nxos_interface: interface=Ethernet admin_state=down host={{ inventory_hostname }}

```

Example 2: Deploy VLANs

Playbook:
```
# example-playbooks/readme-example2.yml
---

- name: example 2 - VLANs
  hosts: all

  tasks:
    - name: ensure VLANs 2-20 and 99 exist on all switches
      nxos_vlan: vlan_id="2-20,99" state=present host={{ inventory_hostname }}

    - name: config VLANs names for a few VLANs
      nxos_vlan: vlan_id={{ item.vid }} name={{ item.name }} host={{ inventory_hostname }} state=present
      with_items:
        - { vid: 2, name: web }
        - { vid: 3, name: app }
        - { vid: 4, name: db }
        - { vid: 20, name: server }
        - { vid: 99, name: native }
```

Example 3: Configure Interfaces

This example has two plays.  One being used to automate the `spine` group and another play being used to automate the `leaf` group.  If you don't have two groups in your `hosts` file, be sure to modify this playbook to meet your requirements.

Playbook:
```
# example-playbooks/readme-example3.yml
---

- name: example 3 - play 1 - spine interfaces
  hosts: spine

  tasks:

    - name: ensure following ports are defaulted
      nxos_interface: interface={{ item }} state=default host={{ inventory_hostname }}
      with_items:
        - Ethernet1/1
        - Ethernet1/2
        - Ethernet1/3
        - Ethernet1/4
        - Ethernet2/9
        - Ethernet2/10
        - Ethernet2/11
        - Ethernet2/12

    - name: vlans for a portchannel
      nxos_switchport: interface={{ item }} mode=trunk native_vlan=99 trunk_vlans=2-20 host={{ inventory_hostname }}
      with_items:
        - Ethernet1/1
        - Ethernet1/2

- name: example 3 - play 2 - leaf interfaces
  hosts: leaf

  tasks:

    - name: ensure ports in scope in this pb are default interfaces
      nxos_interface: interface={{ item }} state=default host={{ inventory_hostname }}
      with_items: leaf_ports

    - name: config for a few interfaces on leafs
      nxos_switchport: interface={{ item }} mode=trunk native_vlan=99 trunk_vlans=2-20 host={{ inventory_hostname }}
      with_items: leaf_ports
    # note: leaf_ports is a variable defined in /home/cisco/nxos-ansible/group_vars/leaf.yml

```

Inside: `/home/cisco/nxos-ansible/group_vars/leaf.yml`

```
---
leaf_ports:
  - Ethernet1/1
  - Ethernet1/2
  - Ethernet1/49
  - Ethernet1/50
  # - ... Continue to include ALL interfaces on the switch
```

Example 4: Configure portchannels

Playbook:
```
# example-playbooks/readme-example4.yml
---

- name: example 4 - play 1 - spine portchannels
  hosts: spine

  tasks:

    - name: portchannel 10 facing a leaf
      nxos_portchannel:
        group: 10
        members: ['Ethernet1/1','Ethernet1/2']
        mode: 'active'
        host: "{{ inventory_hostname }}"
        state: present


- name: example 4 - play 2 - leaf portchannels
  hosts: leaf

  tasks:

    - name: portchannel 100 facing spine
      nxos_portchannel:
        group: 100
        members: ['Ethernet1/1','Ethernet1/2']
        mode: 'active'
        host: "{{ inventory_hostname }}"
        state: present

```

#### Automated Data Collection
The previous examples showed how to use the Cisco Ansible modules to ensure the device configuration is in a desired state.  The next few examples will show how to extract, and then store, data from the Nexus switches.

> **Note.  This example uses the username and password parameters in the playbook.  Feel free to remove them or correct them.**

Example 5: Get neighbors

Playbook:
```
# example-playbooks/readme-example5.yml
---

- name: example 5 - get neighbors
  hosts: spine

  tasks:

    # also showing username/password as params
    # you can remove or insert the correct values

    - name: get neighbors
      nxos_get_neighbors: type=cdp host={{ inventory_hostname }} username=admin password=cisco123

```

This playbook extracts neighbor information from the device.  

**There are a few different options to view the neighbor data from the previous example.**

First, the playbook can be run in verbose mode.  This is done by using the `-v` parameter when running the playbook.  Example: `ansible-playbook readme-example5.yml -v`

```
cisco@onepk:~/nxos-ansible$ ansible-playbook readme-example5.yml -v

PLAY [get neighbor data] ****************************************************** 

TASK: [get neighbors] ********************************************************* 
ok: [n9k1] => {"changed": false, "resource": [{"local_interface": "mgmt0",
"neighbor": "Switch", "neighbor_interface": "GigabitEthernet1/3", "platform":
"cisco WS-C4948-10GE"}, {"local_interface": "Ethernet1/1", "neighbor": "9k3
SAL1834Z8X2)", "neighbor_interface": "Ethernet1/1", "platform": "N9K-C9396PX"}, 
{"local_interface": "Ethernet1/2", "neighbor": "9k4(SAL1834ZDUV)",
"neighbor_interface": "Ethernet1/1", "platform": "N9K-C9396PX"},
{"local_interface": "Ethernet1/3", "neighbor": "9k5(SAL183600CW)",
"neighbor_interface": "Ethernet1/1", "platform": "N9K-C9396PX"},
{"local_interface": "Ethernet1/47", "neighbor": "9k2(SAL1834Z8X1)",
"neighbor_interface": "Ethernet1/47", "platform": "N9K-C9396PX"}]}

PLAY RECAP ******************************************************************** 
n9k1                       : ok=1    changed=0    unreachable=0    failed=0 
```


> Note: Even when configuration changes are being made, you can use the `-v` parameter to extract valuable information.  Many modules return the state of resource being managed before and after the change along with the commands being sent to the device.

Another option is to **register** the return data into a new variable and then use the **debug** module to dump it to the terminal  Take a look.

Plabyook:
```
---

- name: get neighbor data
  hosts: n9k1

  tasks:

    - name: get neighbors
      nxos_get_neighbors: type=cdp host={{ inventory_hostname }} username=admin password=cisco123
      register: my_neighbors

    - name: debug neighbor data
      debug: var="{{ my_neighbors.resource }}"
      # You don't need resource here, but you can see from verbose mode, the
      # neighbor data you'd want is in the key=resource
```

Whent this playbook is run for a single device, it looks like this (using a different playbook name here):
```
cisco@onepk:~/nxos-ansible$ ansible-playbook get-neighbors.yml

PLAY [get neighbor data] ****************************************************** 

TASK: [get neighbors] ********************************************************* 
ok: [n9k1]

TASK: [debug neighbor data] *************************************************** 
ok: [n9k1] => {
    "[{u'neighbor_interface': u'GigabitEthernet1/3', u'platform': u'cisco WS-C4948-10GE', 
    u'local_interface': u'mgmt0', u'neighbor': u'Switch'}, {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    'local_interface': u'Ethernet1/1', u'neighbor': u'9k3(SAL1834Z8X2)'},
    {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/2', u'neighbor': u'9k4(SAL1834ZDUV)'},
    {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/3', u'neighbor': u'9k5(SAL183600CW)'},
    {u'neighbor_interface': u'Ethernet1/47', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/47', u'neighbor': u'9k2(SAL1834Z8X1)'}]":
    "[{u'neighbor_interface': u'GigabitEthernet1/3', u'platform': u'cisco WS
    C4948-10GE', u'local_interface': u'mgmt0', u'neighbor': u'Switch'},
    {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/1', u'neighbor': u'9k3(SAL1834Z8X2)'},
    {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/2', u'neighbor': u'9k4(SAL1834ZDUV)'},
    {u'neighbor_interface': u'Ethernet1/1', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/3', u'neighbor': u'9k5(SAL183600CW)'},
    {u'neighbor_interface': u'Ethernet1/47', u'platform': u'N9K-C9396PX',
    u'local_interface': u'Ethernet1/47', u'neighbor': u'9k2(SAL1834Z8X1)'}]"
}

PLAY RECAP ******************************************************************** 
n9k1                       : ok=2    changed=0    unreachable=0    failed=0  
```

And yet another option is to dump the data to a file.  In order to do this, we'll first we'll use a small Jinja2 template that make this look a bit prettier.

We'll store this template in our working directory and call this template neighbors.j2.  The contents of this file is just a single line.

```
{{ my_neighbors.resource | to_nice_json }}
```

Playbook:
```
---

- name: get neighbor data
  hosts: n9k1

  tasks:

    - name: get neighbors
      nxos_get_neighbors: type=cdp host={{ inventory_hostname }} username=admin password=cisco123
      register: my_neighbors

    - name: print data to file
      template: src=neighbors.j2 dest=configs/neighbors.json
      # using the configs dir to store the final data file
      # but any dir can be created and used here
```


Executing this playbook:
```
cisco@onepk:~/nxos-ansible$ ansible-playbook get-neighbors.yml

PLAY [get neighbor data] ****************************************************** 

TASK: [get neighbors] ********************************************************* 
ok: [n9k1]

TASK: [print neighbor data] *************************************************** 
changed: [n9k1]

PLAY RECAP ******************************************************************** 
n9k1                       : ok=2    changed=1    unreachable=0    failed=0   
```

Looking at the contents of the file created at `/home/cisco/nxos-ansible/configs/neighbors.json`

```
cisco@onepk:~/nxos-ansible$ cat configs/neighbors.json 

[
    {
        "local_interface": "mgmt0", 
        "neighbor": "Switch", 
        "neighbor_interface": "GigabitEthernet1/3", 
        "platform": "cisco WS-C4948-10GE"
    }, 
    {
        "local_interface": "Ethernet1/1", 
        "neighbor": "9k3(SAL1834Z8X2)", 
        "neighbor_interface": "Ethernet1/1", 
        "platform": "N9K-C9396PX"
    }, 
    {
        "local_interface": "Ethernet1/2", 
        "neighbor": "9k4(SAL1834ZDUV)", 
        "neighbor_interface": "Ethernet1/1", 
        "platform": "N9K-C9396PX"
    }, 
    {
        "local_interface": "Ethernet1/3", 
        "neighbor": "9k5(SAL183600CW)", 
        "neighbor_interface": "Ethernet1/1", 
        "platform": "N9K-C9396PX"
    }, 
    {
        "local_interface": "Ethernet1/47", 
        "neighbor": "9k2(SAL1834Z8X1)", 
        "neighbor_interface": "Ethernet1/47", 
        "platform": "N9K-C9396PX"
    }
]
cisco@onepk:~/nxos-ansible$ 

```


You also have the flexibility to maniuplate this data and combine it with other data by manipulating the Jinja2 template.

# Example Playbooks

In addition to the examples in the previous sections, more examples have been posted for learning how to use the Cisco Ansible modules.

Feel free to contribute your example playbooks too.

[See here](example-playbooks/)

#  Cisco NX-OS Module Docs

Overview of each module in traditional Ansible style tables format.

[See here](docs/nexus-module-docs.md)

# Requirements

**API**

Nexus switch that supports NX-API 1.0.  You can verify this through the NX-API sandbox (look in the bottom right of your browser after you login to the sandbox at http://<nexus_ip_addr>)

**Privileges**

Proper privileges on the switch.  You can use the pre-defined system role that offers "devops" privileges or use the "network-admin" role.

**Hardware**

Currently, Nexus 3000 and 9000 platforms. 7K/5K coming soon.

Testing was performed on the following platforms:
  * 3064: 6.0(2)U4(1)
  * 9396: 6.1(2)I3(1)

**Software Dependencies**

The modules depend on two Python libraries: `pycsco` and `xmltodict`.  They can both be installed with `pip`.  More detail on `pycsco` can be found [here](https://github.com/jedelman8/pycsco).

# Contributions

Please contribute! Feel free to open issues or pull requests pertaining to the documentation, code, and playbooks, If you have good use cases, feel free to add them to the repo too.


# License

See [here](#license)

# Appendix - Features to Know

Here is a very short list of some other things to know when working with Ansible for the first time.  They can help you save some time!

  * [ansible-doc](#ansible-doc)
  * [Verbose Output](#verbose-output)
  * [Dry Run Check Mode](#Dry-Run-check-mode)

### ansible-doc

Ansible offers built-in documentation (assuming the modules are properly documented).  All of the Cisco modules have been documented, so you can use the `ansible-doc` utility to better understand the parameters each module supports.  Below is one example of using `ansible-doc` for the `nxos_vpc module`.

Be sure to also check out the [Ansible Module Index](http://docs.ansible.com/modules_by_category.html) for much more detail on all of the Ansible core modules.

> Check out the tables [here](docs/nexus-module-docs.md) for the Cisco modules.  These tables resemble those that Ansible has on their site for the core modules.

```
cisco@onepk:~$ ansible-doc nxos_vpc
> NXOS_VPC

  Manages global VPC configuration

Options (= is mandatory):

- auto_recovery
        Enables/Disables auto recovery (Choices: true, false)
        [Default: None]

- delay_restore
        manages delay restore command and config value in seconds
        (Choices: ) [Default: None]

= domain
        VPC domain (Choices: ) [Default: None]

= host
        IP Address or hostname (resolvable by Ansible control host) of
        the target NX-API enabled switch (Choices: ) [Default: None]

- password
        Password used to login to the switch Technically required if
        not using the .netauth file in the home dir of the Ansible
        control host.  That will clean up Ansible playbooks until
        there is native integration. (Choices: ) [Default: None]

- peer_gw
        Enables/Disables peer gateway (Choices: true, false) [Default:
        None]

- pkl_dest
        Destination (remote) IP address used for peer keepalive link
        (Choices: ) [Default: None]

- pkl_src
        Source IP address used for peer keepalive link (Choices: )
        [Default: None]

- pkl_vrf
        VRF used for peer keepalive link (Choices: ) [Default:
        management]

= protocol
        Dictates connection protocol to use for NX-API (Choices: http,
        https) [Default: http]

- role_priority
        Role priority for device. Remember lower is better. (Choices:
        ) [Default: None]

= state
        Manages desired state of the resource (Choices: present,
        absent) [Default: present]

- system_priority
        System priority device.  Remember they must match between
        peers. (Choices: ) [Default: None]

- username
        Username used to login to the switch Technically required if
        not using the .netauth file in the home dir of the Ansible
        control host.  That will clean up Ansible playbooks until
        there is native integration. (Choices: ) [Default: None]

Requirements:  NX-API 1.0, NX-OS 6.1(2)I3(1), nxapi_lib v0.1, device module (for
        Device/Auth instance)

# ensure vpc domain 100 is configured
- nxos_vpc: domain=100 role_priority=1000 system_priority=2000 pkl_src=192.168.100.1 pkl_dest=192.168.100.2 

# ensure peer gateway is enabled for vpc domain 100
- nxos_vpc: domain=100 peer_gw=true host={{ inventory_hostname }}

# ensure vpc domain does not exist on switch
- nxos_vpc: domain=100 host={{ inventory_hostname }} state=absent

```

You can also use `ansible-doc` on the core modules such as `template`.

```
cisco@onepk:~$ ansible-doc template
> TEMPLATE

  Templates are processed by the Jinja2 templating language
  (http://jinja.pocoo.org/docs/) - documentation on the template
  formatting can be found in the Template Designer Documentation
  (http://jinja.pocoo.org/docs/templates/). Six additional variables
  can be used in templates: `ansible_managed' (configurable via the
  `defaults' section of `ansible.cfg') contains a string which can be
  used to describe the template name, host, modification time of the
  template file and the owner uid, `template_host' contains the node
  name of the template's machine, `template_uid' the owner,
  `template_path' the absolute path of the template,
  `template_fullpath' is the absolute path of the template, and
  `template_run_date' is the date that the template was rendered. Note
  that including a string that uses a date in the template will result
  in the template being marked 'changed' each time.

Options (= is mandatory):

- backup
        Create a backup file including the timestamp information so
        you can get the original file back if you somehow clobbered it
        incorrectly. (Choices: yes, no) [Default: no]

= dest
        Location to render the template to on the remote machine.
        [Default: None]

= src
        Path of a Jinja2 formatted template on the local server. This
        can be a relative or absolute path. [Default: None]

- validate
        The validation command to run before copying into place. The
        path to the file to validate is passed in via '%s' which must
        be present as in the visudo example below. validation to run
        before copying into place. The command is passed securely so
        shell features like expansion and pipes won't work. [Default:
        ]

Notes:  Since Ansible version 0.9, templates are loaded with
        `trim_blocks=True'.

# Example from Ansible Playbooks
- template: src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode=0644

# Copy a new "sudoers" file into place, after passing validation with visudo
- template: src=/mine/sudoers dest=/etc/sudoers validate='visudo -cf %s'
```

### Verbose Output

This was already covered in a few of the playbook examples, but using verbose output comes in very handy when troubleshooting.  Don't forget that `-v` and `-vvvv` can be used to get verbose and extremely verbose output.  When running in verbose mode, you will see all data being gathered from the device per task.  Here is an example using the `-v` parameter.

Playbook:
```
---

- name: testing verbose mode
  hosts: n9k1

  tasks:
    - nxos_vlan: vlan_id=10 name=APP_SEGMENT admin_state=up host={{ inventory_hostname }}

```

This task states the desired state is to ensure VLAN 10 exists, it has the name APP_SEGMENT, and the VLAN should be in the up state.

For this example, the switch already has VLAN 10 present, but has the name web_segment and is in the down state.

Let's see what happens when running the playbook in verbose mode.

```
cisco@onepk:~/nxos-ansible$ ansible-playbook onetest.yml -v

PLAY [testing verbose mode] *************************************************** 

TASK: [nxos_vlan vlan_id=10 name=APP_SEGMENT admin_state=up host={{ inventory_hostname }}] *** 
changed: [n9k1] => {"changed": true, "commands": {"10": "vlan 10 ; no shutdown ; 
name APP_SEGMENT ; exit ;"}, "existing": {"10": {"admin_state": "down",
"name": "web_segment", "vlan_id": "10", "vlan_state": "active"}}, "new":
{"10": {"admin_state": "up", "name": "APP_SEGMENT", "vlan_id": "10",
"vlan_state": "active"}}, "proposed": {"admin_state": "up", "name":
"APP_SEGMENT", "vlan_id": "10", "vlan_state": "active"}, "state": "present"}

PLAY RECAP ******************************************************************** 
n9k1                       : ok=1    changed=1    unreachable=0    failed=0   

cisco@onepk:~/nxos-ansible$ 
```

You can see multiple key-value pairs are returned.  They include the commands executed on the switch, but also the existing, new, and proposed values.  These key-value pairs can now be stored in a playbook using the `register` helper module and used as inputs to other tasks or in Jinja2 templates.


### Dry Run Check Mode

You can see which commands are actually pushed when using the `-v` flag, but what about seeing which commands will be sent to the device without actually pushing them?  This is possible by using dry run (or check mode).  In order to use check mode, run the playbook with the `--check` option.  

Here is an example using `--check`:

Playbook:
```
---

- name: testing check mode
  hosts: n9k1

  tasks:
    - nxos_switchport: interface=Ethernet1/1 mode=access access_vlan=10 host={{ inventory_hostname }}

```

This example has a default config on interface Ethernet1/1 and produces the following output when the playbook is run in check mode.

```
cisco@onepk:~/nxos-ansible$ ansible-playbook onetest.yml --check

PLAY [testing check mode] ***************************************************** 

TASK: [nxos_switchport interface=Ethernet1/1 mode=access access_vlan=10 host={{ inventory_hostname }}] *** 
changed: [n9k1]

PLAY RECAP ******************************************************************** 
n9k1                       : ok=1    changed=1    unreachable=0    failed=0  
```

Here you now know there **WILL** be a change when the playbook is run.  To see these commands, add in the `-v` flag to run in verbose mode as shown here:

```
cisco@onepk:~/nxos-ansible$ ansible-playbook onetest.yml --check -v

PLAY [testing check mode] ***************************************************** 

TASK: [nxos_switchport interface=Ethernet1/1 mode=access access_vlan=10 host={{ inventory_hostname }}] *** 
changed: [n9k1] => {"changed": true, "commands": "interface ethernet1/1 ; switchport access vlan 10 ;"}

PLAY RECAP ******************************************************************** 
n9k1                       : ok=1    changed=1    unreachable=0    failed=0 

```

Here you get to see which commands will be sent without actually sending them.  Very helpful for troubleshooting.


----

 

