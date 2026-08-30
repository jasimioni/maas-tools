#!/usr/bin/env python3
#
# Get fabrics.
#
# Usage: get_fabrics.py

'''
You can use the CLI to create snippets. 

maas admin dhcpsnippets --help
maas admin dhcpsnippet --help

https://maas.io/docs/dhcp-snippet


One example for a global one:
maas admin dhcpsnippets create name="Custom Snippet" value="default-lease-time 600;max-lease-time 600;" enabled=True global_snipped=True


You can list the snippets with:
maas admin dhcpsnippets read

Here is a query to quick list the ids:
maas admin dhcpsnippets read | jq -r '.[] | [.id, .name] | @tsv'

You can delete a snippet using its id:
maas admin dhcpsnippet delete <id>

Or update it using:

maas admin dhcpsnippet update <id> + same parameters from create


I'm not sure what you plan to do with this automation, but I believe one thing was to enable static ip addresses for BMC nodes. You can create them like this:

maas admin dhcpsnippets create name="maas-ubuntu02" value="host maas-ubuntu02 { hardware ethernet 52:54:00:f3:62:22; fixed-address 192.168.50.25; }" enabled=True global_snipped=False subnet=192.168.50.0/24

With this you could create one snippet per host. If you prefer, you can also have one snippet with many hosts.

maas admin dhcpsnippets create name="BMC Static Addresses" value="host maas-ubuntu02 { hardware ethernet 52:54:00:f3:62:22; fixed-address 192.168.50.25; }
host maas-ubuntu03 { hardware ethernet 52:54:00:25:de:eb; fixed-address 192.168.50.26; }" enabled=True global_snipped=False subnet=192.168.50.0/24


This is also available in Python 
'''

import json
import os
import sys
import argparse
import re
from requests_oauthlib import OAuth1Session
import http.client
http.client.HTTPConnection.debuglevel = 5


MAAS_API_KEY = '7CvK9pXSHRCxqPb9ce:FL5MDTfVwsSK7CLRQJ:sqn8eXmvtFSSpp2nhMFYAvMEjg5agRaV'
MAAS_URL = 'http://192.168.50.10:5240/'

if __name__ == '__main__':
    
    consumer_key, key, secret = MAAS_API_KEY.split(':')
    session = OAuth1Session(
        consumer_key, resource_owner_key=key, resource_owner_secret=secret
    )
    
    maas_url = MAAS_URL
    url = maas_url.split('/MAAS')[0].rstrip('/') + '/MAAS/api/2.0/dhcp-snippets/'
    
    snippets = session.request('GET', url, verify=False).json()
                        
    url = f"{url}12/"
                        
    params = { 'value': 'Joao' }
                        
    #r = session.request('PUT', url, data=params, verify=False)
    r = session.put(url, data=params, verify=False)
    print("Request Headers (PUT):")
    for k, v in r.request.headers.items():
        print(f"{k}: {v}")
    print("\nRequest Body:")
    print(r.request.body)
    
    print("\nResponse Headers:")
    for k, v in r.headers.items():
        print(f"{k}: {v}")
    
    print(f"Status code: {r.status_code}")
    print(f"Response: {r.text}")
    
    url += 'op-revert'
    
    params = { 'to': -2 }
    
    print(json.dumps(params, indent=2))
    
    r = session.request('POST', url, data=params, verify=False)
    print("\nRequest Headers: (POST)")
    for k, v in r.request.headers.items():
        print(f"{k}: {v}")
    print("\nRequest Body:")
    print(r.request.body)
    print("\nResponse Headers:")
    for k, v in r.headers.items():
        print(f"{k}: {v}")
    
    print(f"Status code: {r.status_code}")
    print(f"Response: {r.text}")
    
    
    
    
    
    
    
    