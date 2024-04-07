#!/usr/bin/env python3

'''
This code is provided as a sample to be used by sysadmins
when creating their own tools. It's not intended to be 
used in production and is not covered by any Canonical support
agreement.
'''

'''
Sample script to check maas services availability

Set the values for MAASURL CANDIDURL RBACURL MAASPROFILE

Directly in the script or using ENV variables. If using env variables
and sudo, remember to use:

sudo -E python3 check_maas.py
'''

import requests, sys, os, json, urllib, subprocess, re
from oauthlib import oauth1
from urllib.parse import urlparse

MAASURL = os.environ.get('MAASURL') or "https://localhost/MAAS"
CANDIDURL = os.environ.get('CANDIDURL') or "https://localhost:8081"
RBACURL = os.environ.get('RBACURL') or "https://localhost:5000"
MAASPROFILE = os.environ.get('MAASPROFILE') or 'admin'

red = lambda s: '\033[91m' + s + '\033[0m'
green = lambda s: '\033[92m' + s + '\033[0m'
yellow = lambda s: '\033[93m' + s + '\033[0m'
gray = lambda s: '\033[90m' + s + '\033[0m'

# Detecting if installation is DEB or SNAP
def detect_installation():
    cmd = subprocess.run(['snap', 'list', 'maas'], capture_output=True)

    if cmd.returncode:
        maasinst='deb'
        maascmd='/usr/bin/maas'
    else:
        maasinst='snap'
        maascmd='/snap/bin/maas'

    return maasinst, maascmd

MAASINST, MAASCMD = detect_installation()

def check_service(service):
    output = subprocess.run(['systemctl', 'is-active', '--quiet', service])
    status = green('ok') if output.returncode == 0 else red('fail')

    print(f"\t{service + ':':14s} {status}")

def check_certificate(url):
    '''
    Expects the URL in the format http[s]://<hostname>[:port]/
    '''

    o = urlparse(url)

    if o.scheme != 'https':
        print(f"\t{'Certificate:':14s} {gray('https not enabled')}")
        return

    host = o.hostname
    port = o.port or 443

    output = subprocess.run(['openssl', 's_client', '-showcerts', '-connect', f'{host}:{port}'], capture_output=True, stdin=subprocess.PIPE)
    output = subprocess.run(['openssl', 'x509', '-inform', 'pem', '-noout', '-text'], capture_output=True, input=output.stdout)
    lines = output.stdout.decode().split("\n")
    n = [i for i, item in enumerate(lines) if re.search('Not After', item)]
    if n:
        match = re.search('Not After\s*:\s(.*)', lines[n[0]])
        expiration = yellow(match.group(1)).lstrip()
    else:
        expiration = red('not found')

    print(f"\t{'Cert expire:':14s} {expiration}")

    n = [i for i, item in enumerate(lines) if re.search('Subject:', item)]
    if n:
        match = re.search('Subject:\s*(.*)', lines[n[0]])
        subject = yellow(match.group(1).lstrip())
        print(f"\t{'Cert subject:':14s} {subject}")


    n = [i for i, item in enumerate(lines) if re.search('X509v3 Subject Alternative Name:', item)]
    if n:
        altnames = yellow(lines[n[0]+1].lstrip())
        print(f"\t{'Cert altnames:':14s} {altnames}")

def check_maas_services():
    print(f"Checking maas services on local server - installation is {MAASINST}:")

    if MAASINST == 'deb':
        services = ( 'maas-http', 'maas-proxy', 'maas-rackd', 'maas-regiond', 'maas-syslog', 'maas-dhcpd', 'named')
        for service in services:
            check_service(service)
    else:
        output = subprocess.run(['snap', 'services', 'maas'], capture_output=True)
        if output.returncode:
            status = yellow('failed to get status')
        else:
            status_line = output.stdout.decode().split("\n")[1]
            name, admin_status, oper_status, *rest = re.split("\s+", status_line)
            if admin_status == 'enabled':
                if oper_status == 'active':
                    status = green(oper_status)
                else:
                    status = red(oper_status)
            else:
                status = yellow(admin_status)

        print(f"\t{'Snap Status:':14s} {status}")


def check_rack_controllers():
    output = subprocess.run([MAASCMD, 'apikey', '--username', MAASPROFILE], capture_output=True)
    apikey = output.stdout.rstrip()

    login = subprocess.run([MAASCMD, 'login', '--insecure', MAASPROFILE, MAASURL, apikey], capture_output=True)

    output = subprocess.run([MAASCMD, MAASPROFILE, 'rack-controllers', 'read', '--insecure'], capture_output=True)
    racks = output.stdout

    print("Checking access to MAAS API")

    try:
        racks = json.loads(racks)
    except Exception as e:
        print(f"\t{'MAAS API':14s} {red('not responding')}")
        return

    print(f"\t{'MAAS API':14s} {green('ok')}")
    check_certificate(MAASURL)

    for rack in racks:
        print(f"Checking Controllers status in: {rack['hostname']}")
        for service in sorted(rack['service_set'], key=lambda x: x['name']):
            status = service['status']
            if status in ['running']:
                status = green(status)
            elif status in ['dead']:
                status = red(status)
            elif status in ['degraded']:
                status = yellow(status)
            else:
                status = gray(status)
            
            if service['status_info'] != '':
                status += f" [{service['status_info']}]"
            print(f"\t{service['name'] + ':':14s} {status}")

def check_candid():
    print("Checking candid on local server")
    output = subprocess.run(['snap', 'services', 'candid'], capture_output=True)
    if output.returncode:
        status = gray('not installed')
    else:
        status_line = output.stdout.decode().split("\n")[1]
        name, admin_status, oper_status, *rest = re.split("\s+", status_line)
        if admin_status == 'enabled':
            if oper_status == 'active':
                status = green(oper_status)
            else:
                status = red(oper_status)
        else:
            status = yellow(admin_status)

    print(f"\t{'Snap Status:':14s} {status}")

    output = subprocess.run(['curl', '-k', CANDIDURL + '/discharge/info'], capture_output=True)
    if output.returncode:
        status = red('unavailable')
    else:
        match = re.search('PublicKey', output.stdout.decode())
        if match:
            status = green('right output')
        else:
            status = red('wrong output') + ' [' + output.stdout.decode().rstrip() + ']'

    print(f"\t{'Discharge URL:':14s} {status}")
    check_certificate(CANDIDURL)

def check_rbac():
    print("Checking canonical-rbac on local server")
    output = subprocess.run(['snap', 'services', 'canonical-rbac'], capture_output=True)
    if output.returncode:
        print(f"\t{'Snap Status:':14s} {gray('not installed')}")
    else:
        status = 'installed'
        for status_line in output.stdout.decode().split("\n")[1:3]:
            name, admin_status, oper_status, *rest = re.split("\s+", status_line)
            prefix, name = re.split("\.", name)
            if admin_status == 'enabled':
                if oper_status == 'active':
                    status = green(oper_status)
                else:
                    status = red(oper_status)
            else:
                status = yellow(admin_status)

            print(f"\t{'Snap ' + name + ':':14s} {status}")

    output = subprocess.run(['curl', '-k', RBACURL + '/status'], capture_output=True)
    if output.returncode:
        status = red('unavailable')
    else:
        try:
            status_json = json.loads(output.stdout)
            assert status_json["config"]["auth"] == "ok" and status_json["config"]["db"] == "ok"
        except Exception as e:
            status = red('wrong output') + ' [' + output.stdout.decode().rstrip() + ']'
            
    print(f"\t{'RBAC URL:':14s} {status}")
    check_certificate(RBACURL)

def check_postgresql():
    print("Checking PostgreSQL on local server")
    check_service('postgresql')

    output = subprocess.run(['pg_isready'], capture_output=True)
    socket, message, *rest = re.split("\s-\s", output.stdout.decode())
    if output.returncode:
        status = red(message.rstrip())
    else:
        status = green(message.rstrip())

    print(f"\t{'Readiness:':14s} {status}")

    output = subprocess.run(['su', 'postgres', '-c', "psql -t -c 'SELECT pg_is_in_recovery()'"], capture_output=True)
    if re.search('t', output.stdout.decode()):
        print(f"\t{'Replication:':14s} {green('secondary')}")
        output = subprocess.run(['su', 'postgres', '-c', "psql -t -c 'SELECT last_msg_receipt_time from pg_stat_wal_receiver'"], capture_output=True)
        result = output.stdout.decode().split("\n")[0].rstrip().lstrip()
        if result == "":
            status = red("no primary info found")
        else:
            status = green("primary info found:") + ' [last update: ' + result + ']'

        print(f"\t{'Primary:':14s} {status}")
    else:
        print(f"\t{'Replication:':14s} {green('primary')}")
        output = subprocess.run(['su', 'postgres', '-c', "psql -t -c 'SELECT reply_time FROM pg_stat_replication'"], capture_output=True)
        result = output.stdout.decode().split("\n")[0].rstrip().lstrip()
        if result == "":
            status = yellow("no replica found")
        else:
            status = green("replica found:") + ' [last update: ' + result + ']'

        print(f"\t{'Secondary:':14s} {status}")

if __name__ == '__main__':
    check_maas_services()
    check_rack_controllers()
    check_candid()
    check_rbac()
    check_postgresql()
