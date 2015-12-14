#!/bin/sh

pythonpath=$(command -v python3 || command -v python)
startstopdeamon="/sbin/start-stop-daemon"

start()
{
	if [ -f "$startstopdeamon" ]; then
		echo "Starting Server ..."
		/sbin/start-stop-daemon --start --background --pidfile drop.pid -m -d ./ --exec $pythonpath -- 'drop_server.py'
	else
		pythonpath qabel-drop/drop_server.py &
	fi
}

stop()
{
	if [ -f "$startstopdeamon" ]; then
		echo "Stopping Server ..."
		/sbin/start-stop-daemon --stop --pidfile drop.pid --remove-pidfile
	else
		lsof -P | grep ':5000' | awk '{print $2}' | xargs kill  
	fi
}

help()
{
	echo "usage:"
	echo "start  -  starts the drop-server"
	echo "stop   -  stops the drop-server"
	echo "python -  get python path"
}



case "$1" in
	"start") start	
		;;
	"stop") stop
		;;
	"python") echo $pythonpath
		;;
	*) help
		;;
esac


