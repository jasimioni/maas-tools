#!/usr/bin/env python3
#
# Get rack_controllers status.
#
# Usage: rack_controller_status.py

import requests, sys, json, urllib
from oauthlib import oauth1

apikey  = 'dJFhLQH9dHPMdr3gGU:eHA62VsuZeC7w7zcz4:Vv65T73KKvFLQuPqZdNN5aYqz6Dz4vaH'
maasurl = 'http://localhost:5240/'

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
    
    h = [ 'hostname', 'service', 'status', 'status_info' ]
    print(f'{h[0]:20s}\t{h[1]:20s}\t{h[2]:15s}\t{h[3]}')
    for controller in json.loads(resp.text):
        hostname = controller['hostname']
        for service in controller['service_set']:
            print(f"{hostname:20s}\t{service['name']:20s}\t{service['status']:15s}\t{service['status_info']}")
