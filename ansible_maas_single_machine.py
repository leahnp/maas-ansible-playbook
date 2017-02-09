#!/usr/bin/env python
import argparse
import json
import re
import sys
import uuid
import os
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
        self.get_node()


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

    def get_node(self):
        headers1 = self.auth()
        headers1['Accept'] = 'application/json'
        url1 = "%s/machines/?op=allocate" % (self.maas.rstrip())
        params = {}
        request1 = requests.post(url1, headers=headers1,params=params)
        # wait for machine
        time.sleep(20) 

        # set variables from allocated machine
        response = json.loads(request1.text)
        deployed_node = response["system_id"]

        # deploy Ubuntu
        headers2 = self.auth()
        headers2['Accept'] = 'application/json'
        url2 = "%s/machines/%s/?op=deploy" % (self.maas.rstrip(), deployed_node)
        request2 = requests.post(url2, headers=headers2)
        # wait for machine to deploy
        time.sleep(200) 

        # get IP address and print
        response2 = json.loads(request2.text)
        deployed_node = response2['interface_set'][0]['links'][0]['ip_address']
        print(deployed_node)


    def cli_handler(self):
        # Manage command line options and arguments
        parser = argparse.ArgumentParser(description='Produce an Ansible inventory from Ubuntu MaaS')
        parser.add_argument('--list', action='store_true', help='List instances by tag (default: True')
        parser.add_argument('--host', action='store', help='Get variables relating to a specific instance')
        parser.add_argument('--nodes', action='store_true', help='List all nodes registered under MaaS')
        self.args = parser.parse_args()

if __name__ == "__main__":
    Inventory()