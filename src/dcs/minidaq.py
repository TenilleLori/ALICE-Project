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
    for i in range(100):
        spacing = 2
        sleepTime = np.random.exponential(scale = spacing)
        time.sleep(sleepTime)
        readevent(ctx, info = "backgound_" + str(spacing) + "s_spacing_exponential")
    #run_period = time.time() + 60*0.5   #How many minutes you want to run it for
    #while (time.time() < run_period):
    #    readevent(ctx)   #TODO: not sure if this works, just skeleton    

@minidaq.command()
@click.pass_context
def trigger_read(ctx):
    run_period = time.time() + 60*0.5 #How long you want to search for triggers for
    #TODO: the rest of this xD

@minidaq.command()
@click.pass_context
def readevent(ctx):
    #TODO: Unblock trigger before each readevent
    #ctx.obj.trdbox.send_string(f"write {su704_pre_base+3} 1")
    print("Collecting data..")
    ctx.obj.trdbox.send_string(f"write 0x08 1") # send trigger
    print(ctx.obj.trdbox.recv_string())
    
    chamber_data = []
    ctx.obj.sfp0.send_string("read") #send request for data from chamber 1
    ctx.obj.sfp1.send_string("read")
    chamber_data.append(ctx.obj.sfp0.recv())
   # ctx.obj.sfp1.send_string("read")
    chamber_data.append(ctx.obj.sfp1.recv())

    dtObj = datetime.now()
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
            eventToFile(event,len(payload), dtObj, chamber_num) # could be len - 1
            chamber_num = 2
        else:
       	    raise ValueError(f"unhandled equipment type 0x{header.equipment_type:0x2}")

def eventToFile(event, eventLength, dateTimeObj, chamber):
    timeStr = dateTimeObj.strftime("%Y-%m-%dT%H:%M:%S.%f")
    fileName = dateTimeObj.strftime("data/daq-%d%b%Y-%H%M%S%f.o32")
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

    # except:
       	# print("File write unsuccessful, ensure there is a directory called 'data' in the current directory")
#    dateTimeObj = datetime.now()
#    filename = dateTimeObj.strftime("data/daq-1-%d%b%Y-%H%M%S%f.txt")
#    try:
#        f = open(filename,'w')
#        f.write("\n".join([str(d) for d in data1]))
#        f.close()
#    except:
#        print("File write unsuccessful, ensure there is a directory called 'data' in the current directory")

    # filename = dateTimeObj.strftime("data/daq-2-%d%b%Y-%H%M%S%f.txt")
    # try:
    #     f = open(filename,'w')
    #     f.write("\n".join([str(d) for d in data2]))
    #     f.close()
    # except:
    #     print("File write unsuccessful, ensure there is a directory called 'data' in the current directory")

    #print(len(data1))
    # print(len(data2))
