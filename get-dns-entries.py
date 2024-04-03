#!/usr/bin/env python3
#
# List DNS Entries
#
# Usage: ./get-dns-entries.py

import requests, sys, json, urllib
from oauthlib import oauth1

apikey  = 'W4ZehZVmn9BGX8rjNF:hbgPbmHtcxwwuraVkK:kafQ88L6kan9S9wkTCKTqeeHwU6E8afv'
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

def get_dnsresources():
    ep = '/MAAS/api/2.0/dnsresources/'
    return request(ep)

if __name__ == '__main__':
    dns_resources = get_dnsresources()
    for res in dns_resources:
        addresses = set()
        for address in res['ip_addresses']:
            if address['ip'] is not None:
                addresses.add(address['ip'])
        print(' '.join( [ res['fqdn'], *addresses ] ))
