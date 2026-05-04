#!/bin/bash

for x in client??
do 
  VM=maas-$x
  MAC=$(virsh dumpxml $VM | grep 'mac address' | cut -f 2 -d "'" | head -n 1)
  maas admin machines create architecture=amd64/generic hostname=$VM mac_addresses="'$MAC'" power_type='virsh' \
                             power_parameters="'{\"power_pass\":\"ubuntu\",\"power_address\":\"qemu+ssh://ubuntu@192.168.122.1/system\",\"power_id\":\"$VM\"}'"
  sleep 120
done
