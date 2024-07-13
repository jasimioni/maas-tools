#!/usr/bin/env python3
#
# monitor-machines-events.py
#
# Sample script to monitor PostgreSQL event CHANNELS (LISTEN/NOTIFY)
# for machines updates and run a custom query after they are seen
#

import psycopg2
from time import localtime, strftime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import select

DB_HOST = 'localhost'
DB_NAME = 'maasdb'
DB_USER = 'maas'
DB_PASS = 'maas'

CHANNELS = [ 'machine_create', 'machine_update', 'machine_delete' ]

machine_status = {
        0  : "New",
        1  : "Commissioning",
        2  : "Failed commissioning",
        3  : "Missing",
        4  : "Ready",
        5  : "Reserved",
        6  : "Deployed",
        7  : "Retired",
        8  : "Broken",
        9  : "Deploying",
        10 : "Allocated",
        11 : "Failed deployment",
        12 : "Releasing",
        13 : "Releasing failed",
        14 : "Disk erasing",
        15 : "Failed disk erasing",
        16 : "Rescue mode",
        17 : "Entering rescue mode",
        18 : "Failed to enter rescue mode",
        19 : "Exiting rescue mode",
        20 : "Failed to exit rescue mode",
        21 : "Testing",
        22 : "Failed testing",
}


def dblistener():
    connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS)

    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = connection.cursor()
    for channel in CHANNELS:
        cur.execute("LISTEN " + channel)
    while True:
        select.select([connection], [], [])
        connection.poll()
        while connection.notifies:
            notify = connection.notifies.pop()
            machine_id = notify.payload

            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "Got NOTIFY:", notify.pid, notify.channel, notify.payload)

            cur.execute('SELECT hostname, status FROM maasserver_node WHERE system_id = %s', (machine_id, ))
            rows = cur.fetchall()
            for hostname, status in rows:
                print("\t", " | ".join( [ machine_id, hostname, machine_status[status] ] ), "\n")

if __name__ == '__main__':
    dblistener()
