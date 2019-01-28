
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
	sudo systemctl stop icegridregistry
	sudo systemctl stop icegridnode
	killall icebox

run-node:
	mkdir -p /tmp/db/node1
	mkdir -p /tmp/db/registry
	icegridnode --Ice.Config=node1.config
	
run-server:  icestorm.config
	./Server.py --Ice.Config=server.config

run-client: icestorm.config
	./Client.py "Downloader1 -t -e 1.1:tcp -h 192.168.1.36 -p 4061 -t 60000" --Ice.Config=client.config
	#La ip debe ajustarse a la que corresponda

run-iceclient: icestorm.config
	./Client.py --Ice.Config=client.config Downloader1

copy-binaries:
	mkdir -p /tmp/mansol
	cp Server.py /tmp/mansol
	cp server.config /tmp/mansol
	cp client.config /tmp/mansol
	cp Client.py /tmp/mansol
	cp downloader.ice /tmp/mansol
	cp work_queue.py /tmp/mansol
	icepatch2calc /tmp/mansol

perm:
	chmod a+x /tmp/db/node1/distrib/mansolDownloader/Server.py
	touch /tmp/db/node1/distrib/mansolDownloader/server-out.txt
	chmod a+rwx /tmp/db/node1/distrib/mansolDownloader/server-out.txt
