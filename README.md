# maas-tools

This is set of general MAAS scripts used for daily troubleshooting and
maintenance.

### check-maas.py

Check MAAS services, consulting systemd / snap, API output and tries to
connect to relevant ports to check certificates and availabibility. Tests
MAAS, Candid and RBAC

### update-certs.py

Wrap the actions required to update certs on MAAS, Candid and RBAC

### create-local-mirror.sh

Generate a local simplestreams mirror, provided by NGINX

### get-dns-entries.py

List DNS entries configured in MAAS

### get-unused-fabrics.py

List fabrics with no machines connected to it. MAAS generates empty fabrics
for unconnected NICs during enlistment / commissioning and depending on the
environment this can get to a high number which would impact performance

### machines-p-query.py

`maas machines read` on big environments usually takes a long time due to some
ORM serialization that is done. This is an attempt to parallelize the read
by querying the machines per fabric.

### monitor-events.py

Read MAAS events to detect machine status changes.

### query-servers.py

Directly query MAAS database to list the machines and some attributes. It is
much faster than API call. Can be used as an example, but may break between
MAAS releases

### show-broken-machines-message.py

[LP#2049661](https://bugs.launchpad.net/maas/+bug/2049661) workaround



