#!/bin/bash
#
# Create a local image mirror to be used by MAAS
# IMAGE_DIR is set to /var/www/html which is the default nginx
# documents folder. This script will also install nginx
# Care if port 80 is already in use as it could potentially break
# the system
#
# Use the information on https://maas.io/docs/mirroring-images-locally 
# to configure MAAS. 
# URL should be: http://localhost/maas/images/ephemeral-v3/stable/
#
# If it complains about a file not found
# (it happens on snap installations) copy the $KEYRING_FILE to the 
# snap var folder (/var/snap/maas/current) and add the path to
# the "Keyring filename" field
#
# /var/snap/maas/current/ubuntu-cloudimage-keyring.gpg

dpkg -l simplestreams | grep -q '^ii' || (echo "Installing simplestreams" && apt install simplestreams -y)
dpkg -l nginx | grep -q '^ii' || (echo "Installing nginx" && apt install nginx -y)

KEYRING_FILE=/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg
IMAGE_SRC=https://images.maas.io/ephemeral-v3/stable
IMAGE_DIR=/var/www/html/maas/images/ephemeral-v3/stable

if [[ -d /var/snap/maas/current && ! -f /var/snap/maas/current/$(basename $KEYRING_FILE) ]]
then
    echo "Copying $KEYRING_FILE to snap folder"
    cp $KEYRING_FILE /var/snap/maas/current/
fi

echo "Mirroring images"
sstream-mirror --keyring=$KEYRING_FILE $IMAGE_SRC $IMAGE_DIR 'arch~(amd64|arm64)' 'release~(bionic|focal|jammy)' --max=1 --progress

echo -e "\nChecking last update times"
curl -s http://localhost/maas/images/ephemeral-v3/stable/streams/v1/index.sjson | grep updated | sed -e 's/^ *//'

echo -en "\nTotal space used: "
du -ksh $IMAGE_DIR
