#!/usr/bin/env python

import argparse
import json
import re
import os
import sys
import uuid
import time

import oauth.oauth as oauth
import requests


class Inventory:

    def __init__(self):
        # set these vars in your terminal
        # export MAAS_API_KEY=<my_api_key>
        # export MAAS_API_URL=http://<my_maas_server>/MAAS/api/2.0
        self.maas = os.environ.get("MAAS_API_URL", None)
        if not self.maas:
            sys.exit("no MAAS_API_KEY environmental variable found. Set this to http<s>://<IP>/MAAS/api/2.0")
        self.token = os.environ.get("MAAS_API_KEY", None)
        if not self.token:
            sys.exit("no MAAS_API_KEY environmental variable found. See https://maas.ubuntu.com/docs/juju-quick-start.html#getting-a-key for getting a MAAS API KEY")
        self.args = None

        # Parse command line arguments
        self.cli_handler()
        self.inventory()

    def auth(self):
        # Split the token from MaaS (Maas UI > username@domain > Account > MaaS Keys)  into its component parts
        (consumer_key, key, secret) = self.token.split(':')
        # Format an OAuth header
        resource_token_string = "oauth_token_secret=%s&oauth_token=%s" % (secret, key)
        resource_token = oauth.OAuthToken.from_string(resource_token_string)
        consumer_token = oauth.OAuthConsumer(consumer_key, "")
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer_token, token=resource_token, http_url=self.maas,
            parameters={'auth_nonce': uuid.uuid4().get_hex()})
        oauth_request.sign_request(
            oauth.OAuthSignatureMethod_PLAINTEXT(), consumer_token, resource_token)
        headers = oauth_request.to_header()
        return headers

    def host(self):
        # Return per host data
        return {}

    def inventory(self):
        ansible = {}

        headers = self.auth()
        headers['Accept'] = 'application/json'
        url = "%s/nodes/" % (self.maas.rstrip())
        request = requests.get(url, headers=headers)

        response = json.loads(request.text)
        group_name = "sea_nuc_list"
        hosts = []
        for server in response:
            hosts.append(server['hostname'])
            ansible[group_name] = {
                "hosts": hosts,
                "vars": {}
                }

        node_dump = self.nodes()

        nodes = {
            '_meta': {
                'hostvars': {}
            }
        }


        # the allocate method will grab an un-allocated node and allocate
        headers1 = self.auth()
        headers1['Accept'] = 'application/json'
        url1 = "%s/machines/?op=allocate" % (self.maas.rstrip())
        request1 = requests.post(url1, headers=headers1)
        # wait for machine
        time.sleep(30) 

        response = json.loads(request1.text)
        deployed_node = response["system_id"]

        # deploy Ubuntu
        headers2 = self.auth()
        headers2['Accept'] = 'application/json'
        url2 = "%s/machines/%s/?op=deploy" % (self.maas.rstrip(), deployed_node)
        request2 = requests.post(url2, headers=headers2)
        # wait for machine
        time.sleep(30) 

        result = ansible.copy()
        result.update(nodes)
        return result

    def nodes(self):
        # Return a list of nodes from the MaaS API (DEBUGGING PURPOSES ONLY)
        headers = self.auth()
        headers['Accept'] = 'application/json'
        # See https://maas.ubuntu.com/docs1.8/api.html for API docs
        url = "%s/nodes/" % self.maas.rstrip()
        request = requests.get(url, headers=headers)
        response = json.loads(request.text)
        return response

    def cli_handler(self):
        # Manage command line options and arguments
        parser = argparse.ArgumentParser(description='Produce an Ansible inventory from Ubuntu MaaS')
        parser.add_argument('--list', action='store_true', help='List instances by tag (default: True')
        parser.add_argument('--host', action='store', help='Get variables relating to a specific instance')
        parser.add_argument('--nodes', action='store_true', help='List all nodes registered under MaaS')
        self.args = parser.parse_args()

if __name__ == "__main__":
    Inventory()