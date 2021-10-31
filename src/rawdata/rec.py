
#!/usr/bin/env python3

import click
import logging
import itertools
import math
# from pprint import pprint

from .header import TrdboxHeader
from .linkparser import LinkParser, logflt
from .logging import ColorFormatter
from .o32reader import o32reader
from .zmqreader import zmqreader

class digits_csv_file:

    def __init__(self,filename="digits.csv", ntimebins=30):
        self.outfile = open(filename,"w")
        self.ntimebins = ntimebins
        self.outfile.write("ev,det,rob,mcm,channel,padrow,padcol")
        for i in range(self.ntimebins):
            self.outfile.write(f",A{i:02}")
        self.outfile.write("\n")
        

    def __call__(self,ev,det,rob,mcm,ch,digits):

    # Convert Readout board and ADC to X/Y-pos
        def conv(rob,mcm,ch):
            '''
            Converts read_out_board and mcm to x and y positions
            Parameters:
	                rob = Readout board
	                mcm = MCM position on ROB
	                ch  = channel within MCM
            returns: x,y position
            '''
            
            mcmcol = 7-(4*(rob%2) + mcm%4)
            row = 4*(math.floor(rob/2)) + math.floor(mcm/4)
            col = 18*mcmcol + ch - 1
        
            return col,row

        # TODO: calculate pad row/column from rob/mcm/channel
        padrow,padcol = conv(rob,mcm,ch)

        # save output to file
        self.outfile.write(f"{ev},{det},{rob},{mcm},{ch},{padrow},{padcol},")
        self.outfile.write(",".join([str(x) for x in digits]))
        self.outfile.write("\n")

@click.command()
@click.argument('source', default='tcp://localhost:7776')
@click.option('-o', '--loglevel', default=logging.INFO)
@click.option('-k', '--skip-events', default=0)
def rec_digits(source, loglevel, skip_events):

    ch = logging.StreamHandler()
    ch.setFormatter(ColorFormatter())
    logging.basicConfig(level=loglevel, handlers=[ch])

    # Run silently
    logflt.set_verbosity(0)


    # Instantiate the reader that will get events and subevents from the source
    if source.endswith(".o32") or source.endswith(".o32.bz2"):
        reader = o32reader(source)
    elif source.startswith('tcp://'):
        reader = zmqreader(source)
    else:
        raise ValueError(f"unknown source type: {source}")

    # The actual parsing of TRD subevents is handled by the LinkParser
    lp = LinkParser(store_digits=digits_csv_file("digits.csv"))

    # Loop through events and subevents
    for evno,event in enumerate(reader):
        lp.next_event()

        if evno<skip_events:
            continue

        for subevent in event.subevents:
            lp.process(subevent.payload)
