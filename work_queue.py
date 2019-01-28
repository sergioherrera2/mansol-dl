#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*-

'''
Simple task queue implementation
'''

import os.path
import sys
from threading import Thread
from queue import Queue

import youtube_dl

import Ice
# pylint: disable=C0413
Ice.loadSlice('downloader.ice')
# pylint: enable=C0413
# pylint: disable=E0401
import Downloader


class NullLogger:
    '''
    Logger used to disable youtube-dl output
    '''
    def debug(self, msg):
        '''Ignore debug messages'''

    def warning(self, msg):
        '''Ignore warnings'''

    def error(self, msg):
        '''Ignore errors'''


# Default configuration for youtube-dl
DOWNLOADER_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': NullLogger()
}


def _download_mp3_(url, destination='./Descargas/'):
    '''
    Synchronous download from YouTube
    '''

    options = {}
    task_status = {}
    def progress_hook(status):
        task_status.update(status)
    options.update(DOWNLOADER_OPTS)
    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([url])
        sys.stdout.write("\033[1;36m")
        print("[INFO] Descarga completada.")
        sys.stdout.write("\033[1;0m")
    
    filename = task_status['filename']
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[:filename.rindex('.') + 1]
    return filename + options['postprocessors'][0]['preferredcodec']
    

class WorkQueue(Thread):
    '''Job Queue to dispatch tasks'''
    QUIT = 'QUIT'
    CANCEL = 'CANCEL'

    def __init__(self,ProgressTopic):
        super(WorkQueue, self).__init__()
        self.queue = Queue()
        self.ProgressTopic = ProgressTopic

    def run(self):
        '''Task dispatcher loop'''
        for job in iter(self.queue.get, self.QUIT):
            self.ProgressTopic.notify(Downloader.ClipData(job.get_url(), Downloader.Status.INPROGRESS))
            #no funciona como se espera (se queda en un bucle eterno)
            try:
                job.download()
                self.ProgressTopic.notify(Downloader.ClipData(job.get_url(), Downloader.Status.DONE))
            except Exception:
                self.ProgressTopic.notify(Downloader.ClipData(job.get_url(), Downloader.Status.ERROR))
                #sys.stderr.write("\033[1;31m")
                #print("[ERROR] Dirección url inválida, no se ha descargado nada.",file=sys.stderr)
                #sys.stdout.write("\033[1;0m")
            self.queue.task_done()

        self.queue.task_done()
        self.queue.put(self.CANCEL)

        for job in iter(self.queue.get, self.CANCEL):
            job.cancel()
            self.queue.task_done()

        self.queue.task_done()

    def add(self, callback, url):
        '''Add new task to queue'''
        print("[INFO] Nueva solicitud de descarga recibida sobre:", url)
        print("[INFO] Descargando...")
        self.ProgressTopic.notify(Downloader.ClipData(url, Downloader.Status.PENDING))
        self.queue.put(Job(callback, url))

    def destroy(self):
        '''Cancel tasks queue'''
        self.queue.put(self.QUIT)
        self.queue.join()


class Job:
    '''Task: clip to download'''
    def __init__(self, callback, url):
        self.callback = callback
        self.url = url

    def get_url(self):
        return self.url
    
    def download(self):
        '''Donwload clip'''
        self.callback.set_result(_download_mp3_(self.url))

    def cancel(self):
        '''Cancel donwload'''
        self.callback.ice_exception(Downloader.SchedulerCancelJob())
