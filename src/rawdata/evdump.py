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
def evdump(source, loglevel, suppress, quiet):

    ch = logging.StreamHandler()
    ch.setFormatter(ColorFormatter())
    logging.basicConfig(level=loglevel, handlers=[ch])

    # Select dwords to suppress
    if quiet >= 1:
        logflt.dword_types['ADC']['suppress'] = True

    if quiet >= 2:
        logflt.dword_types['MSK']['suppress'] = True
        logflt.dword_types['TRK']['suppress'] = True

    if quiet >= 3:
        logflt.dword_types['MCM']['suppress'] = True
        logflt.dword_types['EOT']['suppress'] = True
        logflt.dword_types['EOD']['suppress'] = True

    if quiet >= 4:
        logflt.dword_types['HC1']['suppress'] = True
        logflt.dword_types['HC2']['suppress'] = True
        logflt.dword_types['HC3']['suppress'] = True

    if quiet >= 5:
        logflt.dword_types['HC0']['suppress'] = True

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
    for event in reader:
        for subevent in event.subevents:
            lp.process(subevent.payload)
