#!/usr/bin/env python3

"""
Create a DHCP snippet in MAAS that sets the lease time for a subnet to one week.

This script validates that the requested subnet exists, creates the snippet if
it does not already exist, or updates it when --update is provided.
"""

PROFILE = "admin"
MAAS = "/usr/bin/maas"
BASE_NAME="One week lease: "
SNIPPET_VALUE="default-lease-time 604800; max-lease-time 604800;"

import subprocess
import json
import argparse

parser = argparse.ArgumentParser(description="Create a DHCP snippet in MAAS to set lease time to one week")
parser.add_argument("subnet", help="Subnet CIDR for which to create the DHCP snippet")
parser.add_argument("--update", action="store_true", help="Update an existing DHCP snippet if present")
args = parser.parse_args()

subnets_read = subprocess.check_output([MAAS, PROFILE, "subnets", "read"]).decode("utf-8")
subnets = json.loads(subnets_read)

subnet_cidrs = [subnet['cidr'] for subnet in subnets]

if args.subnet not in subnet_cidrs:
    print(f"Subnet {args.subnet} not found in MAAS")
    exit(1)

snippet_name = BASE_NAME + args.subnet

dhcpsnippets_read = subprocess.check_output([MAAS, PROFILE, "dhcpsnippets", "read"]).decode("utf-8")
dhcpsnippets = json.loads(dhcpsnippets_read)

existing_snippet = next((snippet for snippet in dhcpsnippets if snippet['name'] == snippet_name), None)

if existing_snippet and not args.update:
    print(f"DHCP snippet \"{snippet_name}\" already exists. Use --update to modify it.")
    exit(1)

name_arg = f'name={snippet_name}'
value_arg = f'value={SNIPPET_VALUE}'


if not existing_snippet:
    subprocess.check_call([MAAS, PROFILE, "dhcpsnippets", "create", name_arg, value_arg, f"subnet={args.subnet}"])

elif args.update:
    subprocess.check_call([MAAS, PROFILE, "dhcpsnippet", "update", str(existing_snippet['id']), value_arg])
