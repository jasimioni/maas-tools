#!/usr/bin/env python3

from collections import defaultdict
import subprocess
import json 
import argparse


def run_maas_command(cmd, profile):
    result = subprocess.run(f'maas {profile} {cmd}', shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {result.stderr}")
        exit(1)
    data = json.loads(result.stdout)
    return data

if __name__ == '__main__':
    # Get the list of images used by machines in MAAS
    parser = argparse.ArgumentParser(description='Report used custom images in MAAS')
    parser.add_argument('--profile', default='admin', help='MAAS profile to use')
    args = parser.parse_args()

    maas_machines = run_maas_command('machines read', args.profile)
    maas_images = run_maas_command('boot-resources read', args.profile)

    images = defaultdict()
    machines = defaultdict()

    for image in maas_images:
        if image['type'] != 'Uploaded':
            continue
        images[image['name']] = image
        images[image['name']]['used_count'] = 0


    for machine in maas_machines:
        if machine['status_name'] not in ['Deployed', 'Failed Deployment']:
            continue
        if machine['osystem'] != 'custom':
            continue

        try:
            image = machine['distro_series']
        except KeyError:
            image = '<unknown>'

        machines[machine['hostname']] = images[image]
        images[image]['used_count'] += 1

    # print(json.dumps(machines, indent=2))
    # print(json.dumps(images, indent=2))

    # Calculate column widths
    name_width = max(len(img['name']) for img in images.values()) if images else 10
    name_width = max(name_width, len('Image Name'))
    
    title_width = max(len(img['title']) for img in images.values()) if images else 10
    title_width = max(title_width, len('Image Title'))
    
    used_width = len('Machine Using')

    # Print header
    header = f"{'Image Name':<{name_width}} | {'Image Title':<{title_width}} | {'Machine Using':<{used_width}}"
    print(header)
    print('-' * len(header))

    # Print each image
    for image in images.values():
        name = image['name']
        title = image['title']
        used_count = str(image['used_count'])
        print(f"{name:<{name_width}} | {title:<{title_width}} | {used_count:>{used_width}}")
