#!/usr/bin/env python
import argparse
import base64
import json
import re
import sys
import uuid
import os
import time
import oauth.oauth as oauth
import requests


# set these vars in your terminal
# export MAAS_API_KEY=<my_api_key>
# export MAAS_API_URL=http://<my_maas_server>/MAAS/api/2.0
maas = os.environ.get("MAAS_API_URL", None)
if not maas:
    sys.exit("no MAAS_API_KEY environmental variable found. Set this to http<s>://<IP>/MAAS/api/2.0")
token = os.environ.get("MAAS_API_KEY", None)
if not token:
    sys.exit("no MAAS_API_KEY environmental variable found. See https://maas.ubuntu.com/docs/juju-quick-start.html#getting-a-key for getting a MAAS API KEY")
args = None


# Split the token from MaaS (Maas UI > username@domain > Account > MaaS Keys)  into its component parts
def auth():
    global maas, token, args
    (consumer_key, key, secret) = token.split(':')
    # Format an OAuth header
    resource_token_string = "oauth_token_secret=%s&oauth_token=%s" % (secret, key)
    resource_token = oauth.OAuthToken.from_string(resource_token_string)
    consumer_token = oauth.OAuthConsumer(consumer_key, "")
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer_token, token=resource_token, http_url=maas,
        parameters={'auth_nonce': uuid.uuid4().get_hex()})
    oauth_request.sign_request(
        oauth.OAuthSignatureMethod_PLAINTEXT(), consumer_token, resource_token)
    headers = oauth_request.to_header()
    return headers

# NOTE: following is useful for debugging how your requests 
# are being formatted.
#
#def pretty_print_POST(req):
#    """
#    At this point it is completely built and ready
#    to be fired; it is "prepared".
#
#    However pay attention at the formatting used in 
#    this function because it is programmed to be pretty 
#    printed and may differ from the actual request.
#    """
#    print('{}\n{}\n{}\n\n{}'.format(
#        '-----------START-----------',
#        req.method + ' ' + req.url,
#        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
#        req.body,
#    ))

#req = requests.Request('POST', url, headers=headers, files=params)
#prepared = req.prepare()
#pretty_print_POST(prepared)

def allocate_node():
    headers = auth()
    headers['Accept'] = 'application/json'
    url = "%s/machines/?op=allocate" % (maas.rstrip())
    params = {}
    response = requests.post(url, headers=headers, files=params)
    data = json.loads(response.text)
    return data

def deploy_node(system_id):
    # deploy Ubuntu
    headers = auth()
    headers['Accept'] = 'application/json'
    url = "%s/machines/%s/?op=deploy" % (maas.rstrip(), system_id)
    # PoC for cloud-init
    cloud_init_script = """
#cloud-config
write_files:
  - path: /home/ubuntu/cloud_test.txt
    owner: ubuntu:ubuntu
    content: |
      Birdfont.
      Netcatz.
"""
    user_data = base64.b64encode(cloud_init_script)
    # NOTE: the requests API lets you pass a map of parameters which will
    # be encoded using the multipart/form-data encoding. ***If you
    # pass the obvious of {'user_data': user_data} the user_data part will
    # be encoded like:
    # Content-Disposition: form-data; name="user_data"; filename="user_data"
    # This extra filename property will cause the MAAS API to fail to parse
    # the parameter.
    # Instead, you must pass a tuple with an empty first param
    # to remove the filename parameter and appease MAAS.
    # passing: params = {'user_data': ('', user_data)}
    # will be encoded like:
    # Content-Disposition: form-data; name="user_data"
    params = {'user_data': ('', user_data)}
    response = requests.post(url, headers=headers, files=params)
    data = json.loads(response.text)
    return data

data = allocate_node()
data = deploy_node(data["system_id"])
ip_address = data['interface_set'][0]['links'][0]['ip_address']
print(ip_address)
# ssh into machine with this ip: $ ssh ubuntu@<ip_address>
