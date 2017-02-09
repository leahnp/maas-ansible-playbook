#!/usr/bin/env python

"""
Ubuntu MaaS External Inventory Script for MaaS Tower
====================================================

This script fetches hosts data for Ansible from Ubuntu MaaS, using Tags to identify groups and roles. It is expected
that the script will be copied to Tower within the new Inventory Scripts dialog offered within the interface, where
it will be passed the `--list` argument to invoke the dynamic inventory process.

"""

import argparse
import json
import re
import sys
import uuid

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

        if self.args.list:
            print json.dumps(self.inventory(), sort_keys=True, indent=2)
        elif self.args.host:
            # We're not doing any host specific lookups yet, so just return an empty dict()
            print json.dumps(self.host(), sort_keys=True, indent=2)
        elif self.args.nodes:
            print json.dumps(self.nodes(), sort_keys=True, indent=2)
        else:
            sys.exit(1)

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

    def tags(self):
        # Fetch a list of tags from MaaS.
        headers = self.auth()
        url = "%s/tags/?op=list" % self.maas.rstrip()
        request = requests.get(url, headers=headers)
        response = json.loads(request.text)
        tag_list = []
        matcher = re.compile(r"ansible_")
        for tag in response:
            if re.match(matcher, tag['name']):
                tag_list.append(tag['name'])
        return tag_list

    def inventory(self):
        # Look up hosts by tag(s) and return a dict that Ansible will understand as an inventory
        tags = self.tags()
        ansible = {}
        for tag in tags:
            headers = self.auth()
            url = "%s/tags/%s/?op=nodes" % (self.maas.rstrip(), tag)
            request = requests.get(url, headers=headers)
            response = json.loads(request.text)
            group_name = tag.partition('_')
            hosts = []
            for server in response:
                hosts.append(server['hostname'])

            if len(hosts):
                ansible[group_name[2]] = hosts

        # PS 2015-09-03: Create metadata block for Ansible's Dynamic Inventory
        # The below code gets a dump of ALL nodes in MaaS and then builds out a _meta JSON attribute.
        node_dump = self.nodes()
        nodes = {
            '_meta': {
                'hostvars': {}
            }
        }
        for node in node_dump:
            if not node['tag_names']:
                pass
            else:
                nodes['_meta']['hostvars'][node['hostname']] = {
                    'mac_address': node['macaddress_set'][0]['mac_address'],
                    'system_id': node['system_id'],
                }

        result = ansible.copy()
        result.update(nodes)
        return result

    def host(self):
        # Return per host data
        h = self.args.host
        l = self.inventory()
        m = l['_meta']['hostvars'][h]
        return m

    def nodes(self):
        # Return a list of nodes from the MaaS API (DEBUGGING PURPOSES ONLY)
        headers = self.auth()
        # See https://maas.ubuntu.com/docs1.8/api.html for API docs
        url = "%s/nodes/?op=list" % self.maas.rstrip()
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