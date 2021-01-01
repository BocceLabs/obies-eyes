# David Hoffman
# Dec 29, 2020
# This script starts an imagezmq stream to a host

# this setting aborts the bash script whenever there is a nonzero exit code
set -e

# change CONSTANTS to whatever is relevant for your system
STARTENV='/home/pi/start_py3cv4.sh'
IMAGEZMQ_PATH='/home/pi/imagezmq_example'
SERVER='Davids-MBP'

# set the PORT based on the hostname
if [ "$(echo $HOSTNAME)" = "rpi4b8gb" ]; then
    PORT='5557'
elif [ "$(echo $HOSTNAME)" = "rpi4b4gb" ]; then
    PORT='5556'
elif [ "$(echo $HOSTNAME)" = "rpi4b2gb" ]; then
    PORT='5555'
elif [ "$(echo $HOSTNAME)" = "rpi3bplus" ]; then
    PORT='5558'
else
    echo "INVALID HOSTNAME"
fi

# activate the environment
echo "====starting the virtual environment (and sleeping 10s)===="
export WORKON_HOME=$HOME/dev/virtenv
export PROJECT_HOME=$HOME/dev
source /usr/local/bin/virtualenvwrapper.sh
sleep 2s
source /home/pi/.virtualenvs/py3cv4/bin/activate
sleep 1s

# cd into the path
echo "====cd into the imagezmq path===="
cd $IMAGEZMQ_PATH

# starting the stream
echo "====starting the stream===="
#if pgrep python; then pkill python; fi
kill -9 `cat save.pid`
rm save.pid
which python
echo "server: " $SERVER
echo "port: " $PORT
# start the client, save output/error to log file, and save the PID (program ID) so we can kill it next time
nohup python client.py --server-ip $SERVER --server-port $PORT > my.log 2>&1 &
echo $! > save.pid

#nohup python test.py &
echo "success"



