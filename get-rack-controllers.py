#!/usr/bin/env python3
#
# Get rack_controllers.
#
# Usage: get_rack_controllers.py

import requests, sys, json, urllib
from oauthlib import oauth1

apikey  = 'em65wT7dK3PWDyxPMy:7fT6n45ZTf7sLM5p89:SZutdqMAhCdZjk2yqzs2dCcsYZaQnscW'
maasurl = 'http://192.168.122.125:5240/'

ep = '/MAAS/api/2.0/rackcontrollers/'

def sign_get_request(apikey, url, headers):
    a1, a2, a3 = apikey.split(':')
    method = 'GET'
    oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')
    url, signed_headers, body = oauth_client.sign(url, method, None, headers)
    return url, signed_headers

if __name__ == '__main__':
    url = urllib.parse.urljoin(maasurl, ep)

    headers = { 'Content-Type': 'application/json' }
    url, signed_headers = sign_get_request(apikey, url, headers)
    resp = requests.get(url, headers=signed_headers, verify=False)
    print(json.dumps(json.loads(resp.text), indent=2))
