#!/usr/bin/python3 -u
# -*- mode:python; coding:utf-8; tab-width:4 -*-

import sys
import os
import binascii

import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
import Downloader

from work_queue import WorkQueue


class SchedulerFactoryI(Downloader.SchedulerFactory):
    def __init__(self, work_queue):
        self.work_queue = work_queue
        
    def make(self, nombre, current = None):
        serverid = Ice.stringToIdentity(nombre)
        dl = DownloadSchedulerI(self.work_queue)
        proxy = current.adapter.add(dl,serverid)
        return Downloader.DownloadSchedulerPrx.checkedCast(proxy)
    
    def kill(self, nombre, current = None): 
        serverid = Ice.stringToIdentity(nombre)
        current.adapter.remove(serverid)
    """    
    def availableSchedulers(self, current = None):
    """


class DownloadSchedulerI(Downloader.DownloadScheduler):
    def __init__(self, work_queue):
        self.work_queue = work_queue

        self.download_path = os.getcwd() + '/Descargas'
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def getSongList(self, current=None):
        return [arch.name for arch in os.scandir(os.getcwd() + '/Descargas') if arch.is_file()]

    def addDownloadTask(self, url, current=None):
        f = Ice.Future()
        self.work_queue.add(f, url)
        return f
    
    def get(self, song, current = None):
        print("[INFO] Nueva solicitud de copia del servidor recibida (", song, ")")
        song = './Descargas/' + song
        try:
        	servant = TransferI(song)
        	proxy = current.adapter.addWithUUID(servant)
        	return Downloader.TransferPrx.checkedCast(proxy)
        except FileNotFoundError as e:
        	print("[ERROR] La canción escrita no existe en el servidor.")   

class TransferI(Downloader.Transfer):
    '''
    Transfer file
    '''
    def __init__(self, local_filename):
        self.file_contents = open(local_filename, 'rb')

    def recv(self, size, current=None):
        '''Send data block to client'''
        return str(binascii.b2a_base64(self.file_contents.read(size), newline=False))

    def end(self, current=None):
        '''Close transfer and free objects'''
        self.file_contents.close()
        current.adapter.remove(current.id)
        print("\033[1;36m")
        print("[INFO] Solicitud de copia del servidor completada.")
        print("\033[1;0m")
        print()

class Server(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {0} not set".format(key))
            return None

        print("Using IceStorm in: {0}".format(key))
        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def run(self, argv):
        topic_mgr = self.get_topic_manager()

        if not topic_mgr:
            print(': Invalid proxy')
            return 2

        topic_name = "ProgressTopic"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        publisher = topic.getPublisher()
        progress_topic = Downloader.ProgressEventPrx.uncheckedCast(publisher)

        work_queue = WorkQueue(progress_topic)

        servant = SchedulerFactoryI(work_queue)
        broker = self.communicator()

        adapter = broker.createObjectAdapter('DlAdapter')
        print("[ADAPTER]", adapter.add(servant, broker.stringToIdentity("dl1")))
        adapter.activate()
       
        work_queue.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        work_queue.destroy()
        return 0

sys.exit(Server().main(sys.argv))
