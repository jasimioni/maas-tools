#!/usr/bin/env python3
#
# list_servers.py
#
# Sample script to run a query to get all machines from a MAAS database. Tested on MAAS 3.2
# Should be run as the maas or root user to have access to /etc/maas/regiond.conf
# And get the database credentials.
#

import psycopg2
import re
import json
from datetime import datetime

machine_status = {
        '0'  : "New",
        '1'  : "Commissioning",
        '2'  : "Failed commissioning",
        '3'  : "Missing",
        '4'  : "Ready",
        '5'  : "Reserved",
        '10' : "Allocated",
        '9'  : "Deploying",
        '6'  : "Deployed",
        '7'  : "Retired",
        '8'  : "Broken",
        '11' : "Failed deployment",
        '12' : "Releasing",
        '13' : "Releasing failed",
        '14' : "Disk erasing",
        '15' : "Failed disk erasing",
        '16' : "Rescue mode",
        '17' : "Entering rescue mode",
        '18' : "Failed to enter rescue mode",
        '19' : "Exiting rescue mode",
        '20' : "Failed to exit rescue mode",
        '21' : "Testing",
        '22' : "Failed testing",
}


def get_db_credentials(file='/etc/maas/regiond.conf'):
    db = {}
    f = open(file, "r")
    for x in f:
        x = x.strip()
        match = re.search("database_(.*):\s+(.*)", x)
        if match:
            var, value = match.groups()
            db[var] = value
    if 'port' not in db:
        db['port'] = 5432

    return db

def list_machines():
    db = get_db_credentials()
    conn = psycopg2.connect(host=db['host'],
                            database=db['name'],
                            user=db['user'], 
                            password=db['pass'],
                            port=db['port'])

    cur = conn.cursor()
    cur.execute('''
WITH ips AS (
	  SELECT maasserver_numanode.node_id, string_agg(host(ip), ', ') ip_list 
		FROM maasserver_numanode, maasserver_nodedevice, maasserver_interface_ip_addresses, maasserver_staticipaddress 
	   WHERE physical_interface_id IS NOT NULL 
		 AND physical_interface_id = maasserver_interface_ip_addresses.interface_id 
		 AND maasserver_staticipaddress.id = maasserver_interface_ip_addresses.staticipaddress_id 
		 AND maasserver_numanode.id = maasserver_nodedevice.numa_node_id 
		 AND ip IS NOT NULL
	GROUP BY maasserver_numanode.node_id
), disks AS (
	SELECT node_config_id, string_agg(name || ':' || size, ', ') disk_list FROM maasserver_blockdevice GROUP BY node_config_id
) SELECT maasserver_node.id, system_id, hostname, description, instance_power_parameters, power_parameters->>'power_address' bmc_address, ip_list,
     maasserver_node.status, hostname || '.' ||  maasserver_domain.name fqdn, power_state, cpu_count cpus, maasserver_node.memory, disks.disk_list 
     FROM maasserver_node 
LEFT JOIN maasserver_domain ON maasserver_domain.id = maasserver_node.domain_id     
LEFT JOIN maasserver_bmc ON maasserver_bmc.id = maasserver_node.bmc_id
LEFT JOIN ips ON ips.node_id = maasserver_node.id
LEFT JOIN maasserver_nodeconfig ON maasserver_node.id = maasserver_nodeconfig.node_id
LEFT JOIN disks ON maasserver_nodeconfig.id = disks.node_config_id
ORDER BY maasserver_node.id
''')

    rows = cur.fetchall()
    colnames = [ desc[0] for desc in cur.description ]

    output = []

    for row in rows:
        row_values = {}
        for i, name in enumerate(colnames):
            row_values[name] = row[i]
        
        row_values['ip_list'] = [] if row_values['ip_list'] is None else row_values['ip_list'].split(", ")
        try:
            row_values['status'] = machine_status[str(row_values['status'])]
        except:
            pass

        disks = []
        if row_values['disk_list'] is not None:
            for disk_size in row_values['disk_list'].split(", "):
                disk, size = disk_size.split(':')
                disks.append( { "name" : disk, "size" : size } )
        row_values['disk_list'] = disks

        output.append(row_values)

    return output

if __name__ == '__main__':
    machines = list_machines()
    print(json.dumps({
        'machines' : machines,
        'timestamp' : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, indent=2))
