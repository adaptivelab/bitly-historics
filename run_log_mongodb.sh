#!/bin/sh
echo "Starting mongo"
mongod --config=./mongodb.conf & 
sleep 2
# tail the log named in the config file 
LOG_PATH=`grep -o "^logpath=.*" mongodb.conf | cut -b 9-`
echo "Tailing" $LOG_PATH
tail -f $LOG_PATH
