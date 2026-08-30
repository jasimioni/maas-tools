#!/usr/bin/env python3

from maasclient import MAASClient
import json
import sys
import argparse
import os

# os.environ['MAAS_API_KEY'] = '7CvK9pXSHRCxqPb9ce:FL5MDTfVwsSK7CLRQJ:sqn8eXmvtFSSpp2nhMFYAvMEjg5agRaV'
# os.environ['MAAS_URL'] = 'http://192.168.50.10:5240/MAAS/'

import random

def generate_random_mac_address():
    """Generates a random MAC address."""
    mac_parts = []
    for _ in range(6):
        # Generate a random integer between 0 and 255
        byte = random.randint(0x00, 0xFF)
        # Convert to a two-digit hexadecimal string and append to list
        mac_parts.append(f"{byte:02x}")
    
    # Join the parts with colons to form the MAC address
    return ":".join(mac_parts)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create a subnet in MAAS")
    parser.add_argument('--apikey', help='MAAS API key. Can be provided using MAAS_API_KEY environment variable.')
    parser.add_argument('--url', help='MAAS URL. Can be provided using MAAS_URL environment variable.')
    parser.add_argument('--hostname', help='Hostname for the new machine. If not provided, a random hostname will be generated.')
    parser.add_argument('--mac', help='MAC address for the new machine. If not provided, a random MAC address will be generated.')
    parser.add_argument('--power-type', help='Power type for the new machine (e.g., "ipmi", "virsh", etc.). If not provided, defaults to "ipmi".')
    parser.add_argument('--power-address', help='Power host for the new machine. Required if power type is not "manual" (qemu+ssh://ubuntu@192.168.122.1/system).')
    parser.add_argument('--power-user', help='Power user for the new machine. Required if power type is not "manual".')
    parser.add_argument('--power-pass', help='Power password for the new machine. Required if power type is not "manual".')
    
    args = parser.parse_args()
    
    apikey = args.apikey or os.environ.get('MAAS_API_KEY') 
    if not apikey:
        sys.exit("MAAS API key not provided")
    
    url = args.url or os.environ.get('MAAS_URL')
    if not url:
        sys.exit("MAAS URL not provided")

    client = MAASClient(apikey, url)
    mac_address = args.mac or generate_random_mac_address()
    hostname = args.hostname or f'test-machine-{mac_address.replace(":", "-")}'
    power_type = args.power_type or 'manual'

    power_address = args.power_address
    power_user = args.power_user
    power_pass = args.power_pass
    results = client.create_machine(hostname=hostname, mac_addresses=[mac_address], power_type=power_type, power_address=power_address, power_user=power_user, power_pass=power_pass)
    if results.status_code != 200:
        print(f"Failed to create machine: {results.text}")
        sys.exit(1)
    print(json.dumps(results.json(), indent=2))