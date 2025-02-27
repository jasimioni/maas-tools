#!/usr/bin/python3
# License MIT
import requests
import json
import time
import threading
import urllib
import os
import asyncio
from oauthlib import oauth1

# MAAS Configuration
maas_url = "<MAAS API ENDPOINT>"
api_key = "<MAAS API KEY>"
# Deployment Configuration / One system_id per line
deployment_queue_file = "deployment_queue.txt"
max_concurrent_deploys = 3
# Deployment Manager / Event Monitor Check Interval
check_interval = 15
# Release Delay
release_delay = 10

# Global variables
current_deployments = set()
last_event_id = 0

def sign_get_request(apikey, url, headers):
    a1, a2, a3 = apikey.split(':')
    method = 'GET'
    oauth_client = oauth1.Client(a1, '', a2, a3, signature_method=oauth1.SIGNATURE_PLAINTEXT, realm='OAuth')
    url, signed_headers, body = oauth_client.sign(url, method, None, headers)
    return url, signed_headers    

def print_colored(text, color='green'):
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }
    color_code = colors.get(color.lower(), colors["reset"])
    print(f"{color_code}{text}{colors['reset']}")


def get_maas_events():
    """ Fetches the latest MAAS events """
    url = urllib.parse.urljoin(maas_url, '/MAAS/api/2.0/events/')
    params = {
        'level' : 'INFO',
        'op'    : 'query',
        'limit' : 10
    }

    if last_event_id > 0:
        params['after'] = last_event_id
        print_colored(f"Read Events, Last Event ID {last_event_id}", "green")
    else:
        print_colored(f"Read Events, Initial Call", "green")

    url_params = '&'.join([f"{key}={params[key]}" for key in params.keys()])
    url += f'?{url_params}'

    headers = { 'Content-Type': 'application/json' }
    url, signed_headers = sign_get_request(api_key, url, headers)

    try:
        resp = requests.get(url, headers=signed_headers, verify=True)
        resp.raise_for_status()
        if resp.text.strip():
            return resp.json().get("events", [])
        else:
            print_colored("Warning: Empty response from MAAS API")
            return []
    except requests.exceptions.RequestException as e:
        print_colored(f"Error reading MAAS events: {e}")
        return []
    except json.JSONDecodeError:
        print_colored(f"Error: Unable to parse JSON. Raw response: {resp.text}")
        return []

def monitor_events():
    """ Monitor MAAS events to track granular deployment progress """
    asyncio.set_event_loop(asyncio.new_event_loop())
    global current_deployments
    global last_event_id
    while True:
        events = get_maas_events()
        
        for event in events:
            #print_colored(event)
            last_event_id = event.get("id")
            system_id = event.get("node")
            if event.get("type") == "Configuring OS":
                print_colored(f"{system_id} is in Configuring OS state (EM)", "white")
                current_deployments.discard(system_id)
                deploy_next_from_queue()
            elif event.get("type") in ["Deployed", "Failed Deployment"]:
                print_colored(f"{system_id} is in Post Deployment state (EM)", "blue")
                current_deployments.discard(system_id)

        time.sleep(check_interval)


def deploy_next_from_queue():
    """ Deploy the next available machine from the queue """
    queue = read_deployment_queue()
    if queue:
        system_id = queue.pop(0)
        print_colored(f"Pull {system_id} from the queue (EM)", "cyan")
        if system_id not in current_deployments:
            release_machine(system_id)
            deploy_machine(system_id)
            current_deployments.add(system_id)
            update_deployment_queue(system_id)


def read_deployment_queue():
    """ Read system IDs from the queue file """
    try:
        with open(deployment_queue_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def update_deployment_queue(completed_id):
    """ Remove completed system ID from the queue """
    queue = read_deployment_queue()
    queue = [id for id in queue if id != completed_id]
    with open(deployment_queue_file, "w") as f:
        if queue:
            f.write("\n".join(queue))


def deploy_machine(system_id):
    """ Deploy a machine in MAAS """
    
    url = f"{maas_url}/MAAS/api/2.0/machines/{system_id}/op-deploy" 
    headers = {'Content-Type': 'application/json'}
    url, signed_headers = sign_get_request(api_key, url, headers)
    
    data = json.dumps({"action": "deploy"})
    try:
        resp = requests.post(url, headers=signed_headers, data=data, verify=True)
        resp.raise_for_status()
        print_colored(f"Deployment started for {system_id}", "magenta")
    except requests.exceptions.RequestException as e:
        print_colored(f"Failed to deploy {system_id}: {e}", "red")


def release_machine(system_id):
    """ Release a machine in MAAS """
    
    url = f"{maas_url}/MAAS/api/2.0/machines/{system_id}/op-release" 
    headers = {'Content-Type': 'application/json'}
    url, signed_headers = sign_get_request(api_key, url, headers)
    
    data = json.dumps({"action": "release"})
    try:
        resp = requests.post(url, headers=signed_headers, data=data, verify=True)
        resp.raise_for_status()
        print_colored(f"Release started for {system_id}", "yellow")
        """ Give Release Time to Complete """
        time.sleep(5)
    except requests.exceptions.RequestException as e:
        print_colored(f"Failed to release {system_id}: {e}", "red")


def deployment_manager():
    """ Manage deployments by ensuring only N machines are deployed at a time """
    asyncio.set_event_loop(asyncio.new_event_loop())
    while True:
        queue = read_deployment_queue()
        available_slots = max_concurrent_deploys - len(current_deployments)
        
        for _ in range(available_slots):
            if queue:
                system_id = queue.pop(0)
                print_colored(f"Pull {system_id} from the queue (DM)", "cyan")
                if system_id not in current_deployments:
                    release_machine(system_id)
                    deploy_machine(system_id)
                    current_deployments.add(system_id)
                    update_deployment_queue(system_id)
        
        time.sleep(check_interval)


def main():
    """ Kick Start Deployments """
    threading.Thread(target=deployment_manager, daemon=True).start()
    """ Wait a little bit before monitoring events """
    time.sleep(30)
    """ Kick Start Monitoring Events """
    threading.Thread(target=monitor_events, daemon=True).start()
    """ Keep The main Thread live """
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()

