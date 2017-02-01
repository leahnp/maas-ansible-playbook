# maas-ansible-playbook
PoC Ansible Playbook to spin up MAAS, acquire node, install os + package

Original ticket: https://github.com/samsung-cnct/k2/issues/142

To use, export environment variables:

        - export MAAS_API_KEY=<my_api_key>
        - export MAAS_API_URL=http://<my_maas_server>/MAAS/api/2.0

And set 'remote user' in ansible.cfg.