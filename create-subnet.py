#!/usr/bin/env python3

from maasclient import MAASClient
import json
import sys
import argparse
import os

description = """
Create a subnet in MAAS

This script creates a subnet in MAAS. It requires the MAAS API key and URL to be provided as arguments.

A subnet must live in a VLAN, so the script first creates a fabric and a VLAN in that fabric. Then it creates a subnet in that VLAN.
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create a subnet in MAAS")
    parser.add_argument('--apikey', help='MAAS API key. Can be provided using MAAS_API_KEY environment variable.')
    parser.add_argument('--url', help='MAAS URL. Can be provided using MAAS_URL environment variable.')
    
    parser.add_argument('--cidr', help='CIDR of the subnet')
    parser.add_argument('--gateway', help='Gateway IP address of the subnet')
    
    args = parser.parse_args()
    
    apikey = args.apikey or os.environ.get('MAAS_API_KEY') 
    if not apikey:
        sys.exit("MAAS API key not provided")
    
    url = args.url or os.environ.get('MAAS_URL')
    if not url:
        sys.exit("MAAS URL not provided")

    client = MAASClient(apikey, url)
    results = client.create_fabric()
    fabric_id = results['id']
    vlan_id = results['vlans'][0]['id']

    results = client.create_subnet(vlan_id=vlan_id, cidr=args.cidr, gateway_ip=args.gateway)
    print(json.dumps(results, indent=2))