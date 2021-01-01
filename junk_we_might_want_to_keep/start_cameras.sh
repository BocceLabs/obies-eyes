#!/bin/bash

# username and password of Pi
username="pi"
password="raspberry"

# all rpi camera hosts
# rpi4b8gb \
# rpi4b4gb \
# rpi4b2gb)
pi_hosts=(rpi3bplus \
    )


# NOTE: Be sure to update client_bash.sh to include the port number!!!

# connect and start the bash script
for i in "${pi_hosts[@]}"
do
	sshpass -p $password ssh -t -t $username@$i 'bash -s' < ./client_bash.sh
done
