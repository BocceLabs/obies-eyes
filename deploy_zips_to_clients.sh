#!/bin/bash

# the ZIP FILE NAME with PATH ((((( no spaces around = sign )))))
zippath=obie_imagezmq
zipfile=obie_imagezmq.zip

# zip it up
zip -r $zipfile $zippath

# username and password of Pi
username="pi"
password="raspberry"

# all rpi camera hosts
pi_hosts=(pict1birdeast   \
          pict1birdmid    \
          pict1birdwest   \
          pict1playereast \
          pict1playerwest)
          #pict1observer)


# NOTE: Be sure to update client_bash.sh to include the port number!!!

# connect and start the bash script
for i in "${pi_hosts[@]}"
do
	sshpass -p $password scp $zipfile $username@$i:~

done

#  'bash -s' < ./client_bash.sh
