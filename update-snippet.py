#!/usr/bin/env python3

from maasclient import MAASClient
import json
import sys
import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create a subnet in MAAS")
    parser.add_argument('--apikey', help='MAAS API key. Can be provided using MAAS_API_KEY environment variable.')
    parser.add_argument('--url', help='MAAS URL. Can be provided using MAAS_URL environment variable.')
    
    parser.add_argument('--snippet-id', required=True, help='ID of the DHCP snippet to update')
    parser.add_argument('--value', required=True, help='New value for the DHCP snippet')
    
    args = parser.parse_args()
    
    apikey = args.apikey or os.environ.get('MAAS_API_KEY') 
    if not apikey:
        sys.exit("MAAS API key not provided")
    
    url = args.url or os.environ.get('MAAS_URL')
    if not url:
        sys.exit("MAAS URL not provided")

    client = MAASClient(apikey, url)
    
    machines = client.machines()
    print(machines)
    
    results = client.update_dhcpsnippet(snippet_id='12', value=args.value, description='Updated snippet value')
    print(results)
    print(json.dumps(results, indent=2))
