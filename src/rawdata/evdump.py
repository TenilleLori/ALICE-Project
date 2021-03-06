#!/usr/bin/env python3

import click
import logging
import itertools
# from pprint import pprint

from .header import TrdboxHeader
from .linkparser import LinkParser, logflt
from .logging import ColorFormatter
from .o32reader import o32reader
from .zmqreader import zmqreader

@click.command()
@click.argument('source', default='tcp://localhost:7750')
@click.option('-o', '--loglevel', default=logging.INFO)
@click.option('-s', '--suppress', multiple=True)
@click.option('-q', '--quiet', count=True)
@click.option('-k', '--skip-events', default=0)
def evdump(source, loglevel, suppress, quiet, skip_events):

    ch = logging.StreamHandler()
    ch.setFormatter(ColorFormatter())
    logging.basicConfig(level=loglevel, handlers=[ch])

    # Select dwords to suppress
    logflt.set_verbosity(5-quiet)
    for s in suppress:
        logflt.dword_types[s.upper()]['suppress'] = True


    # Instantiate the reader that will get events and subevents from the source
    if source.endswith(".o32") or source.endswith(".o32.bz2"):
        reader = o32reader(source)
    elif source.startswith('tcp://'):
        reader = zmqreader(source)
    else:
        raise ValueError(f"unknown source type: {source}")

    # The actual parsing of TRD subevents is handled by the LinkParser
    lp = LinkParser()

    # Loop through events and subevents
    for evno,event in enumerate(reader):
        if evno<skip_events:
            continue
        if not event[0]:
            for subevent in event.subevents:
                lp.process(subevent.payload)
        else:
            print("wave at time: " + event.timestamp.strftime("%d%b%Y-%H%M%S%f"))
            wave_print(event.payload)

def wave_print(arr):
    for i in range(len(arr)//3):
        print(str(arr[3*i])+', '+str(arr[3*i+1])+', '+str(arr[3*i+2]))
