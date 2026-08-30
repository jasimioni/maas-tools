# maas-tools

This is set of general MAAS scripts used for daily troubleshooting and
maintenance.

### add-machine.py

Create a new machine in MAAS with hostname, MAC address and power settings.
Supports manual and non-manual power types.

### bulk-create-subnet.py

Create multiple subnets in MAAS from a CSV-style input, creating fabrics and
VLANs when needed.

### check-maas.py

Check MAAS services, consulting systemd / snap, API output and tries to
connect to relevant ports to check certificates and availabibility. Tests
MAAS, Candid and RBAC

### update-certs.py

Wrap the actions required to update certs on MAAS, Candid and RBAC

### create-local-mirror.sh

Generate a local simplestreams mirror, provided by NGINX

### create-subnet.py

Create a single subnet in MAAS and automatically create/select the target
fabric and VLAN.

### create_vms_in_maas.sh

Discover local libvirt VMs and register them in MAAS with virsh power
parameters.

### get-dns-entries.py

List DNS entries configured in MAAS

### get-fabrics.py

List fabrics configured in MAAS.

### get-machines-in-fabrics.py

List machines in MAAS and filter output by one or more fabric names.

### get-rack-controllers.py

List rack controllers known by MAAS.

### maas-deployment-watcher.py

Queue and monitor machine deployments by tracking MAAS events and progressing
machines through deployment states.

### maasclient.py

Helper MAAS API client used by other scripts. Wraps OAuth1 requests and common
operations for machines, fabrics, subnets and DHCP snippets.

### manage-dhcp-static-addesses.py

Generate and manage DHCP snippets to assign static addresses (for example BMC
or host interfaces) through MAAS.

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

### monitor-machines-events.py

Listen directly to MAAS database event channels (PostgreSQL LISTEN/NOTIFY) to
show machine create/update/delete events in real time.

### oauth-put.py

Example script for authenticated OAuth PUT/POST calls against MAAS API
endpoints (DHCP snippets), useful for request debugging.

### query-servers.py

Directly query MAAS database to list the machines and some attributes. It is
much faster than API call. Can be used as an example, but may break between
MAAS releases

### show-broken-machines-message.py

[LP#2049661](https://bugs.launchpad.net/maas/+bug/2049661) workaround

### rack-controller-status.py

Print rack controller status and services in a tabular summary.

### report-used-custom-images.py

Report custom images uploaded to MAAS and show how many deployed machines use
each image.

### update-snippet.py

Update an existing MAAS DHCP snippet value/description by snippet id.



