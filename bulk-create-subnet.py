#!/usr/bin/env python3

from maasclient import MAASClient
import json
import sys
import argparse
import os
import csv

description = """
Create subnets in MAAS reading if from a CSV file

Expect a CSV file in the format:

    cidr,gateway
    
A subnet must live in a VLAN, so the script first creates a fabric and a VLAN in that fabric. Then it creates a subnet in that VLAN.
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--apikey', help='MAAS API key. Can be provided using MAAS_API_KEY environment variable.')
    parser.add_argument('--url', help='MAAS URL. Can be provided using MAAS_URL environment variable.')
    parser.add_argument('file', help='CSV file with the subnets to create')
    args = parser.parse_args()

    apikey = args.apikey or os.environ.get('MAAS_API_KEY') 
    if not apikey:
        sys.exit("MAAS API key not provided")
    
    url = args.url or os.environ.get('MAAS_URL')
    if not url:
        sys.exit("MAAS URL not provided")

    client = MAASClient(apikey, url)
    
    with open(args.file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            cidr, gateway = row
    
            results = client.create_fabric()
            fabric_id = results['id']
            vlan_id = results['vlans'][0]['id']

            results = client.create_subnet(vlan_id=vlan_id, cidr=cidr, gateway_ip=gateway)
            print(json.dumps(results, indent=2))