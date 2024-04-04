#!/usr/bin/env python3

'''
usage: update-certs.py [-h] --key KEY --cert CERT [--chain CHAIN] [--ca CA] [--candid] [--rbac] [--maas] [--maas-port MAAS_PORT] [--all] [--force] [--backup | --no-backup]

Update MAAS related certificates

options:
  -h, --help            show this help message and exit
  --key KEY             Certificate key file
  --cert CERT           Certificate file
  --chain CHAIN         Certificate Chain file
  --ca CA               Certificate Authority file
  --candid              Update Candid Cert (if needed)
  --rbac                Update RBAC Cert (if needed)
  --maas                Update MAAS Cert (if needed)
  --maas-port MAAS_PORT
                        MAAS SSL Port (Default is 443)
  --all                 Update all certs (same as --maas --rbac --candid)
  --force               Update even if the cert is the same
  --backup, --no-backup
                        Perform a backup of the changed items (default: True)
'''

import argparse
import logging
import os
import shutil
import subprocess
import yaml
from datetime import datetime
from cryptography import x509

def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data"""
    if data.count('\n') > 0:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def detect_maas_installation():
    cmd = subprocess.run(['snap', 'list', 'maas'], capture_output=True)

    if cmd.returncode:
        maasinst='deb'
        maascmd='/usr/bin/maas'
    else:
        maasinst='snap'
        maascmd='/snap/bin/maas'

    return maasinst, maascmd

def get_cert_data(cert):
    try:
        cert_data = x509.load_pem_x509_certificate(cert)
        return cert_data.serial_number, cert_data.subject.rfc4514_string(), cert_data.not_valid_after
    except:
        return None, None, None

def update_maas(cert_file, key_file, chain_file=None, ca_file=None, force=False, backup=True, port=443,
                backup_suffix = '.' + datetime.now().strftime('%Y%m%d%H%M%S')):
    logging.info("Checking if maas needs update.")


    maasinst, maascmd = detect_maas_installation()

    if maasinst == 'deb':
        maas_config_folder='/var/lib/maas/http/certs'
        tmp_dir = os.path.join('/tmp/', backup_suffix)
    else:
        maas_config_folder='/var/snap/maas/current/http/certs'
        tmp_dir = os.path.join('/var/snap/maas/current', backup_suffix)

    regiond_cert_file = os.path.join(maas_config_folder, 'regiond-proxy.pem')

    with open(regiond_cert_file, 'r') as f:
        cert = str.encode(f.read())

    serial_number, subject, expiration = get_cert_data(cert)

    with open(cert_file, 'r') as f:
        new_cert = str.encode(f.read())

    n_serial_number, n_subject, n_expiration = get_cert_data(new_cert)

    install = 1
    if n_serial_number == serial_number and n_subject == subject and n_expiration == expiration:
        logging.info(f"The certs are the same: {subject} valid until {expiration}. Requires --force")
        install = 0

    if install or force:
        logging.info("Installing new maas certs")

        if backup:
            shutil.copytree(maas_config_folder, maas_config_folder + backup_suffix)

        chained_cert = ''
        for file in (cert_file, chain_file, ca_file):
            if file is not None:
                with open(file) as f: 
                    chained_cert += f.read()

        certs = []

        lines = chained_cert.split('\n')
        for line in lines:
            if 'BEGIN CERTIFICATE' in line:
                current_cert = []
            current_cert.append(line)
            if 'END CERTIFICATE' in line:
                certs.append('\n'.join(current_cert))

        os.makedirs(tmp_dir)
        tmp_key_file = os.path.join(tmp_dir, 'cert.key')
        tmp_cert_file = os.path.join(tmp_dir, 'cert.crt')
        tmp_chain_file = os.path.join(tmp_dir, 'chain.crt')

        cmd = [ maascmd, 'config-tls', 'enable', tmp_key_file, tmp_cert_file, '--yes', '-p', port ]

        shutil.copy(key_file, tmp_key_file)

        with open(tmp_cert_file, 'w') as outfile:
            outfile.write(certs[0])

        if len(certs) > 1:
            with open(tmp_chain_file, 'w') as outfile:
                outfile.write('\n'.join(certs[1:]))
            cmd.extend([ '--cacert', tmp_chain_file ])


        subprocess.run(cmd)

        shutil.rmtree(tmp_dir)

def update_candid(cert_file, key_file, chain_file=None, ca_file=None, force=False, backup=True,
                  candid_config_file='/var/snap/candid/current/config.yaml',
                  backup_suffix = '.' + datetime.now().strftime('%Y%m%d%H%M%S')):
    logging.info("Checking if candid needs update.")

    with open(candid_config_file, 'r') as config:
        candid_config = yaml.safe_load(config)

    cert = str.encode(candid_config['tls-cert'])
    serial_number, subject, expiration = get_cert_data(cert)

    with open(cert_file, 'r') as f:
        new_cert = str.encode(f.read())

    n_serial_number, n_subject, n_expiration = get_cert_data(new_cert)

    install = 1
    if n_serial_number == serial_number and n_subject == subject and n_expiration == expiration:
        logging.info(f"The certs are the same: {subject} valid until {expiration}. Requires --force")
        install = 0

    if install or force:
        logging.info("Installing new candid certs")
        with open(key_file) as f:
            key = f.read()

        chained_cert = ''
        for file in (cert_file, chain_file, ca_file):
            if file is not None:
                with open(file) as f: 
                    chained_cert += f.read()
        candid_config['tls-cert'] = chained_cert
        candid_config['tls-key'] = key

        if backup:
            shutil.copyfile(candid_config_file, candid_config_file + backup_suffix)

        with open(candid_config_file, 'w') as outfile:
            yaml.dump(candid_config, outfile, sort_keys=False)

        subprocess.run([ 'snap', 'stop', 'candid' ])
        subprocess.run([ 'snap', 'start', 'candid' ])

def update_rbac(cert_file, key_file, chain_file=None, ca_file=None, force=False, backup=True,
                rbac_config_folder='/var/snap/canonical-rbac/current/conf',
                backup_suffix = '.' + datetime.now().strftime('%Y%m%d%H%M%S')):
    logging.info("Checking if rbac needs update.")

    run = subprocess.run(["snap", "get", "canonical-rbac", "ssl.cert"], capture_output=True)
    cert = run.stdout
    serial_number, subject, expiration = get_cert_data(cert)

    with open(cert_file, 'r') as f:
        new_cert = str.encode(f.read())

    n_serial_number, n_subject, n_expiration = get_cert_data(new_cert)

    install = 1
    if n_serial_number == serial_number and n_subject == subject and n_expiration == expiration:
        logging.info(f"The certs are the same: {subject} valid until {expiration}. Requires --force")
        install = 0

    if install or force:
        logging.info("Installing new rbac certs")

        if backup:
            shutil.copytree(rbac_config_folder, rbac_config_folder + backup_suffix)

        crbs_py_file = os.path.join(rbac_config_folder, 'crbs.py')
        uwsgi_ini_file = os.path.join(rbac_config_folder, 'uwsgi.ini')

        shutil.copy2(crbs_py_file, crbs_py_file + backup_suffix)
        shutil.copy2(uwsgi_ini_file, uwsgi_ini_file + backup_suffix)

        with open(key_file) as f:
            key = f.read()

        chained_cert = ''
        for file in (cert_file, chain_file):
            if file is not None:
                with open(file) as f: 
                    chained_cert += f.read()

        cmd = [ 'snap', 'set', 'canonical-rbac', f'ssl.key={key}', f'ssl.cert={chained_cert}' ]

        if ca_file is not None:
            with open(ca_file) as f:
                ca_cert = f.read()
            cmd.append(f'ssl.ca={ca_cert}')

        subprocess.run(cmd)

        shutil.move(crbs_py_file + backup_suffix, crbs_py_file)
        shutil.move(uwsgi_ini_file + backup_suffix, uwsgi_ini_file)

        subprocess.run([ 'snap', 'stop', 'canonical-rbac' ])
        subprocess.run([ 'snap', 'start', 'canonical-rbac' ])


if __name__ == '__main__':
    yaml.add_representer(str, str_presenter)
    logging.basicConfig(level=logging.INFO)

    desc = """
    Update MAAS related certificates
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--key",
        help="Certificate key file",
        required=True,
    )
    parser.add_argument(
        "--cert",
        help="Certificate file",
        required=True,
    )
    parser.add_argument(
        "--chain",
        help="Certificate Chain file",
    )
    parser.add_argument(
        "--ca",
        help="Certificate Authority file",
    )
    parser.add_argument(
        "--candid",
        help='Update Candid Cert (if needed)',
        action='store_true'
    )
    parser.add_argument(
        "--rbac",
        help='Update RBAC Cert (if needed)',
        action='store_true'
    )
    parser.add_argument(
        "--maas",
        help='Update MAAS Cert (if needed)',
        action='store_true'
    )
    parser.add_argument(
        "--maas-port",
        help='MAAS SSL Port (Default is 443)',
        default='443'
    )
    parser.add_argument(
        "--all",
        help='Update all certs (same as --maas --rbac --candid)',
        action='store_true'
    )
    parser.add_argument(
        "--force",
        help='Update even if the cert is the same',
        action='store_true'
    )
    parser.add_argument(
        "--no-backup",
        help='Does not perform a backup of the changed items',
        action='store_true'
    )

    args = parser.parse_args()

    backup = not args.no_backup

    assert os.path.isfile(args.cert), f"Could not open {args.cert}"
    assert os.path.isfile(args.key), f"Could not open {args.key}"
    if args.chain:
        assert os.path.isfile(args.chain), f"Could not open {args.chain}"
    if args.ca:
        assert os.path.isfile(args.ca), f"Could not open {args.ca}"

    if args.all or args.candid:
        update_candid(cert_file=args.cert, key_file=args.key, chain_file=args.chain, ca_file=args.ca, force=args.force, backup=backup)

    if args.all or args.rbac:
        update_rbac(cert_file=args.cert, key_file=args.key, chain_file=args.chain, ca_file=args.ca, force=args.force, backup=backup)

    if args.all or args.maas:
        update_maas(cert_file=args.cert, key_file=args.key, chain_file=args.chain, ca_file=args.ca, force=args.force, port=args.maas_port, backup=backup)
