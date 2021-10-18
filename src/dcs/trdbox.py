
import click
import zmq

class TrdboxCommand:
    def __init__(self, connect):

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(connect)

    def exec(self, cmd):
        self.socket.send_string(cmd)
        return self.socket.recv_string()


@click.group()
@click.option('-c', '--connect', default='tcp://localhost:7766')
@click.pass_context
def trdbox(ctx, connect):
    ctx.obj = TrdboxCommand(connect)


@trdbox.command()
@click.argument('cmd', default=1)
@click.pass_context
def pretrigger(ctx, cmd):
    ctx.obj.exec(f"write 0x08 {cmd}")

@trdbox.command()
@click.argument('sfp')
@click.argument('cmd')
@click.pass_context
def sfp(ctx, sfp, cmd):
    ctx.obj.exec(f"sfp{sfp} {cmd}")

@trdbox.command()
@click.argument('address', callback=lambda c,p,x: int(x,0))
@click.pass_context
def read(ctx, address):
    rd = int(ctx.obj.exec(f"read {address}"),16)
    print(f"Read from 0x{address:04x}: {rd} = 0x{rd:08x}")

@trdbox.command()
@click.argument('address', callback=lambda c,p,x: int(x,0))
@click.argument('data', callback=lambda c,p,x: int(x,0))
@click.pass_context
def write(ctx, address, data):
    ctx.obj.exec(f"write {address} {cmd}")
