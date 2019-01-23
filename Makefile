
all:

clean:
	$(RM) *~
	$(RM) -r db

start:  icebox.config icestorm.config
	@if ! [ -d db ]; then mkdir db; fi
	icebox --Ice.Config=icebox.config &
	sleep 3
	icestormadmin --Ice.Config=icestorm.config -e "create ProgressTopic"

stop: icestorm.config
	icestormadmin --Ice.Config=icestorm.config -e "destroy ProgressTopic"
	killall icebox

run-publisher:  icestorm.config
	./Server.py --Ice.Config=publisher.config

run-subscriber: icestorm.config
	./Client.py "dl1 -t -e 1.1:tcp -h 192.168.1.37 -p 9090 -t 60000" --Ice.Config=subscriber.config 
