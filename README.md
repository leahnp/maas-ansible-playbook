# Maas Ansible Playbook

This describes a script that allocates a single node on MAAS, passes a custom cloud-init task and deploys an operating system on the machine. This script returns the IP address for the machine that you can use to run an Ansible task which installs a package. This was a research project and proof of concept.

## Installation

Using Ansible 2.2.1.0 and MAAS API version 2.0. 

## Usage

To use, export environment variables:

        - export MAAS_API_KEY=<my_api_key>
        - export MAAS_API_URL=http://<my_maas_server>/MAAS/api/2.0

Run the script to allocate node, run cloud-init and deploy operating system. 

  `./ansible_maas_single_machine.py`

When the script is complete, take the IP address in the output and run: 

  `ansible-playbook -i <IP>, -u ubuntu -e 'ansible_python_interpreter=/usr/bin/python3' install_pkg.yml`

NOTES: Ubuntu 16.04 LTS "Xenial Xerus" comes with Python3, so you must explicitly tell Ansible where to find Python to run Ansible tasks.

If you want to run your ansible task on more than one machine, put them in a comma separated list after the first IP.

You can find information about setting up your ssh keys in the MAAS dashboard.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

Original ticket: https://github.com/samsung-cnct/k2/issues/142

Things to consider with Ansible-MAAS integration:
  - Since the machines I was using for this exercise did not have operating systems Ansible could not ssh onto the machine to do the first task of allocating and deploying an os. 
  - You can have your "inventory" script return the machines you want Ansible to you by passing -i script.py
