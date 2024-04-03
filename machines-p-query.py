#!/usr/bin/env python3

import json, sys, os, time, re
import asyncio
import aiohttp
import requests

from urllib.parse import urljoin
from oauthlib import oauth1
import argparse

class MaasRequest:
    def __init__(self, apikey, url):
        self.apikey = apikey
        self.url = url
        a1, a2, a3 = self.apikey.split(':')
        self.oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')

    def _get(self, ep, params):
        headers = { 'Content-Type': 'application/json' }
        url = urljoin(self.url, ep)
        method = 'GET'

        if params is not None:
            filter = []
            for key in params.keys():
                if type(params[key]) == list:
                    for item in params[key]:
                        filter.append(f'{key}={item}')
                else:
                    filter.append(f'{key}={params[key]}')
            url += '?' + '&'.join(filter) 

        uri, signed_headers, body = self.oauth_client.sign(url, method, None, headers)

        return uri, signed_headers

    def machines(self, params=None):
        ep = '/MAAS/api/2.0/machines/'
        return self._get(ep, params)

    def fabrics(self, params=None):
        ep = '/MAAS/api/2.0/fabrics/'
        return self._get(ep, params)

async def get_machines(session, url, headers):
    async with session.get(url, headers=headers, ssl=False) as resp:
        machines = await resp.json()
        return machines

async def p_fetch_machines(apikey, url, groupsize=5, parallel=6, fabrics_re=''):
    parallel = int(parallel)
    groupsize = int(groupsize)

    maas = MaasRequest(apikey, url)

    fabrics = []
    async with aiohttp.ClientSession() as session:
        uri, headers = maas.fabrics()
        async with session.get(uri, headers=headers, ssl=False) as resp:
            response = await resp.json()
            for fabric in response:
                if re.search(fabrics_re, fabric['name']):
                    fabrics.append(fabric['name'])

    connector = aiohttp.TCPConnector(limit=parallel)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(0, len(fabrics), groupsize):

            fabric_list = fabrics[i:i+groupsize]

            uri, headers = maas.machines(params={ 'fabrics' : fabric_list })
            tasks.append(asyncio.ensure_future(get_machines(session, uri, headers)))

        machines = await asyncio.gather(*tasks)

        machine_data = {}

        for machine_list in machines:
            for machine in machine_list:
                machine_data[machine['system_id']] = machine

        machines = []
        for system_id in machine_data.keys():
            machines.append(machine_data[system_id])
        
        print(json.dumps(machines, indent=2))

if __name__ == '__main__':
    desc = """
    List all machines in TOR fabrics
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--apikey",
        help="API Key",
        required=True,
    )
    parser.add_argument(
        "--url",
        help="MAAS URL (no /MAAS needed)",
        required=True,
    )
    parser.add_argument(
        "--fabrics_re",
        help="regex to match fabric names",
        default='',
        required=False,
    )
    parser.add_argument(
        "--groupsize",
        help="Group fabrics by this ammount - default 5",
        default=5,
        required=False,
    )
    parser.add_argument(
        "--parallel",
        help="Number of concurrent requestes - default 6",
        default=6,
        required=False,
    )
    args = parser.parse_args()

    asyncio.run(p_fetch_machines(args.apikey, args.url, groupsize=args.groupsize, parallel=args.parallel, fabrics_re=args.fabrics_re))
