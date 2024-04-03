#!/usr/bin/env python3
#
# Monitor MAAS events to detect servers status change
# to trigger machines updates
# 
# Usage: monitor_events.py

import requests, sys, json, urllib, os
from oauthlib import oauth1

apikey  = 'm7nj2dRuXhyFZAPLkk:aALYngddEDsjv5NUpQ:cn4Wcu79zmjTCLwLPx2jcmH9qLHNC5Bw'
maasurl = 'http://localhost:5240/'

last_event_store_file = '.last_event'

ep = '/MAAS/api/2.0/events/'

def get_last_event(last_event_store_file):
    if os.path.isfile(last_event_store_file):
        with open(last_event_store_file) as event_store:
            try:
                return int(event_store.read().rstrip())
            except:
                pass
    return None

def save_last_event(last_event_store_file, ev):
    with open(last_event_store_file, 'w') as event_store:
        event_store.write(f'{ev}')

def sign_get_request(apikey, url, headers):
    a1, a2, a3 = apikey.split(':')
    method = 'GET'
    oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')
    url, signed_headers, body = oauth_client.sign(url, method, None, headers)
    return url, signed_headers

if __name__ == '__main__':
    url = urllib.parse.urljoin(maasurl, ep)

    params = {
        'level' : 'INFO',
        'op'    : 'query',
        'limit' : 1000
    }

    last_event = get_last_event(last_event_store_file)

    if last_event:
        params['after'] = last_event

    url_params = '&'.join([ f"{key}={params[key]}" for key in params.keys() ])

    url += f'?{url_params}'

    print(url)

    headers = { 'Content-Type': 'application/json' }
    url, signed_headers = sign_get_request(apikey, url, headers)
    resp = requests.get(url, headers=signed_headers, verify=False)
    data = json.loads(resp.text)

    for event in sorted(data['events'], key=lambda ev: ev['id']):
        last_event = event['id']
        print('\t'.join([event['node'], event['hostname'], str(event['id']), event['level'], event['created'], event['type'], event['description']]))
        if event['type'] in [ 'Marking node failed', 'Deployed', 'Ready', 'Released', 'New', 'Aborted deployment', 'Rescue mode', 'Exited rescue mode' ]:
            print(f"Trigger a machine update for {event['node']} as the new status is {event['type']}")

    save_last_event(last_event_store_file, last_event)
