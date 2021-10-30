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
from typing import NamedTuple
from datetime import datetime

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
@click.pass_context
def background_read(ctx):
    run_period = time.time() + 60*0.5   #How many minutes you want to run it for
    while (time.time() < run_period):
        readevent(ctx)   #TODO: not sure if this works, just skeleton    

@minidaq.command()
@click.pass_context
def trigger_read(ctx, n_events=5):
    #run_period = time.time() + 60*0.5 #How long you want to search for triggers for
    trig_count_1 = int(os.popen('trdbox reg-read 0x102').read().split('\n')[0])
    trig_count_2 = 0
    i = 0
    timestamp = datetime.now()
    while i <= (n_events):
        trig_count_2 = int(os.popen('trdbox reg-read 0x102').read().split('\n')[0])

        if trig_count_2 != trig_count_1:
            i += 1
            print(i) # Just for monitoring purposes

            readevent(ctx,dtObj= timestamp, info="trigger")
            trig_count_1 = trig_count_2
        else:
            pass
@minidaq.command()
@click.pass_context
def readevent(ctx, dtObj = datetime.now(), info=""):
    #Unblock trdbox and dump chamber buffers
    os.system("trdbox unblock")
    os.system("trd dump 0")
    os.system("trd dump 0")       #dump twice as sometimes there are errors
    os.system("trd dump 1")
    os.system("trd dump 1")    

    print("Collecting data..")
    ctx.obj.trdbox.send_string(f"write 0x08 1") # send trigger
    print(ctx.obj.trdbox.recv_string())
       
    chamber_data = []
    ctx.obj.sfp0.send_string("read") #send request for data from chamber 1
    ctx.obj.sfp1.send_string("read")
    chamber_data.append(ctx.obj.sfp0.recv())
    chamber_data.append(ctx.obj.sfp1.recv())

    chamber_num = 1
    for rawdata in chamber_data:
        header = TrdboxHeader(rawdata)
        if header.equipment_type == 0x10:
            payload = np.frombuffer(rawdata[header.header_size:], dtype=np.uint32)
            print(payload)
       	    subevent = subevent_t(header.equipment_type, header.equipment_id, payload)
            event =  event_t(header.timestamp, tuple([subevent]))
            print(subevent)
            print(event.subevents)
            eventToFile(event,len(payload), dtObj, chamber_num, info) # could be len - 1
            chamber_num = 2
        else:
       	    raise ValueError(f"unhandled equipment type 0x{header.equipment_type:0x2}")

def eventToFile(event, eventLength, dateTimeObj, chamber, info):
    timeStr = dateTimeObj.strftime("%Y-%m-%dT%H:%M:%S.%f")
    fileName = dateTimeObj.strftime("data/daq-%d%b%Y-%H%M%S%f-"+info+".o32")
    print(fileName)
    # try:
    f = open(fileName, 'a')
    #Different Header for each chamber
    if (chamber==1):
        f.write("# EVENT\n# format version: 1.0\n# time stamp: "+timeStr+"\n# data blocks: 2\n## DATA SEGMENT\n## sfp: 0\n## size: "+str(eventLength)+"\n")
        f.write("\n".join([hex(d) for d in event.subevents[0].payload]))
    else: 
        f.write("\n## DATA SEGMENT\n## sfp: 1\n## size: "+str(eventLength)+"\n")
        f.write("\n".join([hex(d) for d in event.subevents[0].payload]))
    
    f.close()
