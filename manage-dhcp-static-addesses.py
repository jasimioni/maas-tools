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


os.environ['MAAS_API_KEY'] = '7CvK9pXSHRCxqPb9ce:FL5MDTfVwsSK7CLRQJ:sqn8eXmvtFSSpp2nhMFYAvMEjg5agRaV'
os.environ['MAAS_URL'] = 'http://192.168.50.10:5240/'

def parse_args():
    parser = argparse.ArgumentParser(description='Manage DHCP static addresses.')
    parser.add_argument('--basename', help='Base name for the rule (default = "Static Addresses for ")"', default='Static Addresses for ')
    parser.add_argument('--subnet', help='Subnet for the static address')
    parser.add_argument('--mac-address', help='MAC address to assign')
    parser.add_argument('--hostname', help='Hostname for the static address')
    parser.add_argument('--ipaddress', help='IP address to assign')
    parser.add_argument('--apikey', help='MAAS API key. Can be provided using MAAS_API_KEY environment variable.')
    parser.add_argument('--maas-url', help='MAAS URL. Can be provided using MAAS_URL environment variable.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='List all rules that match the basename. If subnet is provided, only list rules for that subnet.')
    group.add_argument('--add', action='store_true', help='Add a static address')
    group.add_argument('--delete', action='store_true', help='Delete a static address')
    
    args = parser.parse_args()
    
    if not args.apikey:
        args.apikey = os.environ.get('MAAS_API_KEY')
        if not args.apikey:
            sys.exit("MAAS API key not provided")
        
    if not args.maas_url:
        args.maas_url = os.environ.get('MAAS_URL')
        if not args.maas_url:
            sys.exit("MAAS URL not provided")
    
    return args

def is_enabled(enabled):
    return 'Enabled' if enabled else 'Disabled'

if __name__ == '__main__':
    args = parse_args()
    
    consumer_key, key, secret = args.apikey.split(':')
    session = OAuth1Session(
        consumer_key, resource_owner_key=key, resource_owner_secret=secret
    )
    
    maas_url = args.maas_url
    url = maas_url.split('/MAAS')[0].rstrip('/') + '/MAAS/api/2.0/dhcp-snippets/'
    
    snippets = session.request('GET', url, verify=False).json()
    for snippet in snippets:
        if snippet['name'].startswith(args.basename):
            if args.subnet:
                if snippet['subnet']['name'] == args.subnet:
                    value = snippet['value']
                    if args.list:
                        print(value)
                    else:
                        content = {}
                        lines = value.split('\n')
                        for line in lines:
                            data = re.match('host\s+(.*?)\s+{ hardware ethernet ([\d\.abcdef:]+).*fixed-address ([\d\.]+)', line, re.IGNORECASE)
                            if data:
                                print(data.groups())
                                name, mac, ip = data.groups()
                                content[name] = { 'mac': mac, 'ip': ip, }
                        if args.delete:
                            del content[args.hostname]
                        elif args.add:
                            content[args.hostname] = {
                                'mac': args.mac_address,
                                'ip': args.ipaddress,
                            }
                        
                        entries = []
                        for name, data in content.items():
                            entries.append(f'host {name} {{ hardware ethernet {data["mac"]}; fixed-address {data["ip"]}; }}')
                        content = '\n'.join(entries)
                        
                        url = f"{url}{snippet['id']}/"
                        
                        print(f"Updating snippet {snippet['id']} with content:\n{content}")
                        
                        params = { 'value': content }
                        files_payload = {}
                        for param in params.keys():
                            files_payload[param] = (None, params[param], 'text/plain; charset="utf-8"')
                        
                        r = session.request('PUT', url, files=files_payload, verify=False)
                        print(r.text)
            else:
                print(f"{snippet['name']}: {is_enabled(snippet['enabled'])} ID: {snippet['id']}")
    
    
    
    
    
    
    
    
    
    