#!/usr/bin/env python3
#
# show_broken_machines_message
# Lists broken machines with the associated message placed
# by the administrator
# 
# Usage: show_broken_machines_message.py

import requests, sys, json, urllib, os
from oauthlib import oauth1

apikey  = 'Q4xxag5Sujs86YhUfP:EgMHU47xEDVBedb9mn:th9RwVTBbX3jYZu3gnAVWAhz5bA39fVj'
maasurl = 'http://localhost:5240/'
headers = { 'Content-Type': 'application/json' }

def sign_get_request(apikey, url, headers):
    a1, a2, a3 = apikey.split(':')
    method = 'GET'
    oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')
    url, signed_headers, body = oauth_client.sign(url, method, None, headers)
    return url, signed_headers

def get_machines(params=None):
    url = urllib.parse.urljoin(maasurl, '/MAAS/api/2.0/machines/')
    if params is not None:
        url_params = '&'.join([ f"{key}={params[key]}" for key in params.keys() ])
        url += '?' + url_params

    url, signed_headers = sign_get_request(apikey, url, headers)
    resp = requests.get(url, headers=signed_headers, verify=False)
    return resp.json()

def get_broken_message(system_id):
    url = urllib.parse.urljoin(maasurl, '/MAAS/api/2.0/events/')
    params = { "id": system_id, "level": "DEBUG", "op": "query" }

    url, signed_headers = sign_get_request(apikey, url, headers)
    url_params = '&'.join([ f"{key}={params[key]}" for key in params.keys() ])
    url += '?' + url_params

    resp = requests.get(url, headers=signed_headers, verify=False)
    events = resp.json()['events']

    for event in events:
        if event['type'] == 'User marking node broken':
            return event['description']
    
if __name__ == '__main__':
    machines = get_machines({ 'status' : 'broken' })

    for machine in machines:
        if machine['status_name'] == 'Broken':
            system_id = machine['system_id']
            message = get_broken_message(system_id)
            machine['broken_message'] = message
            print(json.dumps(machine, indent=2))
