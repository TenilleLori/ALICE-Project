import pickle
import time
import shutil
import click
import zmq
import itertools
from datetime import datetime

from subprocess import Popen
import subprocess
import os
import sys
import numpy as np
import argparse
from struct import unpack
import time
import logging
import dcs.oscilloscopeRead.scopeRead as scopeRead
from typing import NamedTuple
from datetime import datetime
from threading import Thread
# from multiprocessing import Process
import signal

from .header import TrdboxHeader
from .linkparser import LinkParser, logflt
from .logging import ColorFormatter
from .logging import AddLocationFilter

class zmq_env:

    def __init__(self):
       	self.context = zmq.Context()

       	self.trdbox = self.context.socket(zmq.REQ)
       	self.trdbox.connect('tcp://localhost:7766')

       	self.sfp0 = self.context.socket(zmq.REQ)
       	self.sfp0.connect('tcp://localhost:7750')

       	self.sfp1 = self.context.socket(zmq.REQ)
       	self.sfp1.connect('tcp://localhost:7751')
        
class event_t(NamedTuple):
    timestamp: datetime
    subevents: tuple

class subevent_t(NamedTuple):
    equipment_type: int
    equipment_id: int
    payload: np.ndarray

@click.group()
@click.pass_context
def minidaq(ctx):
    ctx.obj = zmq_env()

@minidaq.command()
def setup():
    print("Setting up processes for minidaq..")
    
    commands = [["sudo", "/usr/local/sbin/trdboxd"],["/usr/local/sbin/subevd", "--sfp0-enable=true", "--sfp1-enable=true"]]
      
    processes =[subprocess.Popen(cmd) for cmd in commands]   #Starts the processes in the background
    print("minidaq set up complete.")

@minidaq.command()
def terminate():
    os.system("killall -s SIGKILL subevd")
    os.system("sudo killall trdboxd")
   
    print("Trdbox and subevent builders terminated.")

@minidaq.command()
@click.option('--n_events','-n', default=5, help='Number of background events you want to read.')
@click.pass_context
def background_read(ctx, n_events):
    # Including oscilloscope data in the .o32 file
    scopeReader = scopeRead.Reader("ttyACM3")
    
    dt = datetime.now()
    folderName = dt.strftime("daq-%d%b%Y-%H%M%S%f-background")
    os.system("mkdir data/"+folderName)
    for i in range(n_events):
        print("Reading.."+str(i))
        spacing = 2
        sleepTime = np.random.exponential(scale = spacing)
        print(sleepTime)
        sleepTime = 2
        time.sleep(sleepTime)
        ctx.invoke(readevent, folder=folderName, info='background', reader = scopeReader, bg = True, n = i)

@minidaq.command()
@click.option('--n_events','-n', default=5, help='Number of triggered events you want to read.')
@click.pass_context

def trigger_read(ctx, n_events):
    scopeReader = scopeRead.Reader("ttyACM3")
    #run_period = time.time() + 60*0.5 #How long you want to search for triggers for
    trig_count_1 = int(os.popen('trdbox reg-read 0x102').read().split('\n')[0])
    os.system("trdbox unblock")
    trig_count_2 = 0
    i = 0
    
    dt = datetime.now()
    folderName = dt.strftime("daq-%d%b%Y-%H%M%S%f-trigger")
    os.system("mkdir data/"+folderName)
    
    while i < (n_events):

        trig_count_2 = int(os.popen('trdbox reg-read 0x102').read().split('\n')[0])

        if trig_count_2 != trig_count_1:
            i += 1
            print("Event triggered.."+str(i)) # Just for monitoring purposes

            signal.signal(signal.SIGALRM, handler)
            signal.alarm(10)

            try:
                 ctx.invoke(readevent, folder=folderName, info="trigger",reader=scopeReader, savescope=True, bg = False, n = i)
            except:
                 i -= 1
            try:
                 time.sleep(10)
            except:
                 pass

            trig_count_1 = int(os.popen('trdbox reg-read 0x102').read().split('\n')[0])
            os.system("trdbox unblock")
        else:
            pass
@minidaq.command()
@click.argument('folder', default='')
@click.argument('info',default='')
@click.option('--saveScope', '-s', is_flag=True)
@click.pass_context
def readevent(ctx, folder, info, reader = None, savescope = False, bg = False, n = 0):
    # bFin = False
    # while not bFin:
        #Unblock trdbox and dump chamber buffers
    try:
        os.system("trdbox unblock")
        os.system("trdbox dump 0 >/dev/null 2>&1")
        os.system("trdbox dump 0 >/dev/null 2>&1")       #dump twice as sometimes there are errors
        os.system("trdbox dump 1 >/dev/null 2>&1")
        os.system("trdbox dump 1 >/dev/null 2>&1")    

        print("Collecting data..")
        ctx.obj.trdbox.send_string(f"write 0x08 1") # send trigger
        print(ctx.obj.trdbox.recv_string())
    
        # Including oscilloscope data in the .o32 file
        chamber_data = []
        ctx.obj.sfp0.send_string("read") #send request for data from chamber 1    
        ctx.obj.sfp1.send_string("read")
        # time.sleep(2)
        chamber_data.append(ctx.obj.sfp0.recv())
        chamber_data.append(ctx.obj.sfp1.recv())
        bFin = chamber_data != [] 
    except:
        pass

    waveforms = reader.getData()
    
    chamber_num = 1
    
    timestamp = datetime.now()
    eventDir = folder+"/event-"+str(n)+"-"+info
    scopeDir = folder+"/oscilloscope-"+str(n)+"-"+info
        
    for rawdata in chamber_data:
        header = TrdboxHeader(rawdata)
        if header.equipment_type == 0x10:
            payload = np.frombuffer(rawdata[header.header_size:], dtype=np.uint32)
       	    subevent = subevent_t(header.equipment_type, header.equipment_id, payload)
            event =  event_t(header.timestamp, tuple([subevent]))
            eventToFile(event,len(payload), eventDir, chamber_num) # could be len - 1

            chamber_num = 2
        else:
            pass
       	    # raise ValueError(f"unhandled equipment type 0x{header.equipment_type:0x2}")
    savescope = True
    if header.equipment_type == 0x10 and savescope == True:
        scopeToFile(waveforms,scopeDir)
    else:
        pass
        # raise ValueError(f"unhandled equipment type 0x{header.equipment_type:0x2}")

def eventToFile(event, eventLength, dirName, chamber):
    currentTime = datetime.now()
    timeStr = currentTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    fileName = "data/"+dirName+".o32"
    print(fileName)
    try:
        f = open(fileName, 'a')
        #Different Header for each chamber
        if (chamber==1):
            f.write("# EVENT\n# format version: 1.0\n# time stamp: "+timeStr+"\n# data blocks: 2\n## DATA SEGMENT\n## sfp: 0\n## size: "+str(eventLength)+"\n")
            f.write("\n".join([hex(d) for d in event.subevents[0].payload]))
        else: 
            f.write("\n## DATA SEGMENT\n## sfp: 1\n## size: "+str(eventLength)+"\n")
            f.write("\n".join([hex(d) for d in event.subevents[0].payload]))
            f.write("\n")
    
        f.close()
    except:
        print("Error writing to file, please make sure there is a data folder in the directory you are running this command in")

def scopeToFile(waveforms, dirName):
    currentTime = datetime.now()
    #print(waveforms)
    timeStr = currentTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    fileName = "data/"+dirName+".o32"
    # fileName = dateTimeObj.strftime("data/oscilloscope-daq-%d%b%Y-%H%M%S%f-"+info+".csv")
    f = open(fileName, 'a')
    f.write("# OSCILLOSCOPE\n# format version: 1.0\n# time stamp: "+timeStr+"\n# data blocks: "+str(len(waveforms[0]))+"\n")
    for i in range(len(waveforms[0])):
        #f.write("## WAVE\n## waveform: " + str(i)+"\n## size: " + str(len(waveforms[i])) + "\n")
        #f.write("\n".join([str(d) for d in waveforms[i]]))
        f.write(str(waveforms[0][i])+","+ str(waveforms[1][i]) + "," + str(waveforms[2][i]))
        f.write("\n")
    f.close()
    #print("Error writing to file, please make sure there is a data folder in the directory you are running this command in")

def handler(signum, frame):
    print("trying again")
    raise Exception("stallout")
