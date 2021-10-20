
import click
import zmq
from datetime import datetime

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
@click.pass_context
def readevent(ctx):

    ctx.obj.trdbox.send_string(f"write 0x08 1") # send trigger
    print(ctx.obj.trdbox.recv_string())

    ctx.obj.sfp0.send_string("read")
    rawdata = ctx.obj.sfp0.recv()

    # ctx.obj.sfp1.send_string("read")
    # data2 = ctx.obj.sfp1.recv()

    #rawdata = self.socket.recv()

    header = TrdboxHeader(rawdata)
    if header.equipment_type == 0x10:
        payload = np.frombuffer(rawdata[header.header_size:], dtype=np.uint32)

        subevent = subevent_t(header.equipment_type, header.equipment_id, payload)
        print(event_t(header.timestamp, tuple([subevent])))
        return event_t(header.timestamp, tuple([subevent]))

    else:
        raise ValueError(f"unhandled equipment type 0x{header.equipment_type:0x2}")
    
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

    print(len(data1))
    # print(len(data2))
