
import click
import zmq
import csv
from datetime import datetime

class zmq_env:
    def __init__(self):

        self.context = zmq.Context()

        self.trdbox = self.context.socket(zmq.REQ)
        self.trdbox.connect('tcp://localhost:7766')

        self.sfp0 = self.context.socket(zmq.REQ)
        self.sfp0.connect('tcp://localhost:7750')

        self.sfp1 = self.context.socket(zmq.REQ)
        self.sfp1.connect('tcp://localhost:7751')


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
    data1 = ctx.obj.sfp0.recv()

    # ctx.obj.sfp1.send_string("read")
    # data2 = ctx.obj.sfp1.recv()
    
    dateTimeObj = datetime.now()
    timestamp = dateTimeObj.strftime("%d%b%Y-%H%M%S%f")
    try: 
        f = open("data/1-chamber_timestamp_test.csv",'a',newline='')
        writer = csv.writer(f)
        writer.writerow([timestamp]+[d for d in data1])

        #f.write("\n".join([str(d) for d in data1]))
        f.close()
    except:
        print("File write unsuccessful, ensure there is a directory called 'data' in the current directory")
    
    # filename = dateTimeObj.strftime("data/daq-2-%d%b%Y-%H%M%S%f.txt")
    # try:
    #     f = open(filename,'w')
    #     f.write("\n".join([str(d) for d in data2]))
    #     f.close()
    # except:
    #     print("File write unsuccessful, ensure there is a directory called 'data' in the current directory")

    print(len(data1))
    # print(len(data2))
