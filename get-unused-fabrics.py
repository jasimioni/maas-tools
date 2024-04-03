#!/usr/bin/env python3
#
# List fabrics not in use
#
# Usage: ./get-unused-fabrics.py 

import requests, sys, json, urllib
from oauthlib import oauth1

apikey  = 'RwVJuP3ypfXs5p9wf8:taKDFNRcgD45ka6VmK:jzTDb9CQhFUrYz92EPsLAYtJbGTtU7bN'
maasurl = 'http://localhost:5240/'

def sign_get_request(apikey, url, headers={ 'Content-Type': 'application/json' }):
    a1, a2, a3 = apikey.split(':')
    method = 'GET'
    oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')
    url, signed_headers, body = oauth_client.sign(url, method, None, headers)
    return url, signed_headers

def request(ep):
    url = urllib.parse.urljoin(maasurl, ep)
    url, signed_headers = sign_get_request(apikey, url)
    resp = requests.get(url, headers=signed_headers, verify=False)
    return resp.json()

def get_machines():
    # ep = '/MAAS/api/2.0/machines/?hostname=cl7-m3'
    ep = '/MAAS/api/2.0/machines/'
    return request(ep)

def get_subnets():
    ep = '/MAAS/api/2.0/subnets/'
    return request(ep)

def get_fabrics():
    ep = '/MAAS/api/2.0/fabrics/'
    return request(ep)

if __name__ == '__main__':
    used_fabrics = set()
    machines = get_machines()
    for machine in machines:
        if 'interface_set' not in machine:
            continue
        for interface in machine['interface_set']:
            try:
                fabric_id = interface['vlan']['fabric_id']
                used_fabrics.add(fabric_id)
            except:
                pass

    subnets = get_subnets()
    for subnet in subnets:
        try:
            fabric_id = subnet['vlan']['fabric_id']
            used_fabrics.add(fabric_id)
        except:
            pass
    
    fabrics = get_fabrics()
    for fabric in fabrics:
        fabric_id = fabric['id']
        if fabric_id not in used_fabrics:
            print(f"maas admin fabric delete {fabric_id}")
