import click
import zmq

"""
defining all of the address bases, from lbox_addr.h
"""
su704_pre_base = 0x100
su736_dis_base = 0x280
su738_sfp0_base = 0x400
su738_sfp1_base = 0x500
su707_scsn_base = 0x000

class TrdboxCommand:
    def __init__(self, connect):

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(connect)

    def exec(self, cmd):
        self.socket.send_string(cmd)
        return self.socket.recv_string()


#creates the trdbox set of commands, for use in the command line

@click.group()
@click.option('-c', '--connect', default='tcp://localhost:7766')
@click.pass_context
def trdbox(ctx, connect):
    ctx.obj = TrdboxCommand(connect)


#this command displays all the register names, addresses, and
#the current value of them

@trdbox.command()
@click.pass_context
def status(ctx):

    # from: lbox_addr.h - these are all the register address bases
    #define SU736_BASE          0x280
    #define SU738_BASE_A        0x400
    #define SU738_BASE_B        0x500
    #define SU704_PRE_BASE_A    0x100
    #define SU707_SCSN_BASE_A   0x000


    registers = list((
      dict( name='pre_conf', addr=su704_pre_base+0),
      dict( name='pre_dgg',  addr=su704_pre_base+1),
      dict( name='pre_cnt',  addr=su704_pre_base+2),
      dict( name='pre_stat', addr=su704_pre_base+3),

      # dict( name='dis_dac',  addr=su736_dis_base+0x08), # reads CONF
      # dict( name='dis_led',  addr=su736_dis_base+0x0c), # reads CONF
      dict( name='dis_conf', addr=su736_dis_base+0x0d),
      dict( name='dis_freq0', addr=su736_dis_base+0x00),
      dict( name='dis_freq1', addr=su736_dis_base+0x01),
      dict( name='dis_time0', addr=su736_dis_base+0x04),
      dict( name='dis_time1', addr=su736_dis_base+0x05),
    ))

    for r in registers:
        rd = int(ctx.obj.exec(f"read {r['addr']}"),16)
        print(f"{r['name']:<10} [0x{r['addr']:03x}]: 0x{rd:08x} = {rd}")


#this command unblocks the TRDbox, which is required if
#autoblock is turned on in the pre-conf register

@trdbox.command()
@click.pass_context
def unblock(ctx):
    ctx.obj.exec(f"write {su704_pre_base+3} 1")


#this command changes the delay gate generator times and widths

@trdbox.command()
@click.argument('width0', callback=lambda c,p,x: int(x,0))
@click.argument('time0', callback=lambda c,p,x: int(x,0))
@click.argument('width1', callback=lambda c,p,x: int(x,0))
@click.argument('time1', callback=lambda c,p,x: int(x,0))
@click.pass_context
def set_dgg(ctx, width0, time0, width1, time1):#sets delay gate generator widt
    address = getAddress("pre_dgg")
    if int(width0) < 10:
        width0 = '0' + str(width0)
    if int(time0) < 10:
        time0 = '0' + str(time0)
    if int(width1) < 10:
        width1 = '0' + str(width1)
    if int(time1) < 10:
        time1 = '0' + str(time1)
    value = int('0x' + str(width0) + str(time0) + str(width1) + str(time1), 16)
    write(ctx,address,value)


#this command changes the discriminator thresholds

@trdbox.command()
@click.argument('ch', callback=lambda c,p,x: int(x,0))
@click.argument('thresh', callback=lambda c,p,x: int(x,0))
@click.pass_context
def dis_thr(ctx, ch, thresh):
    value = ( (ch&1) << 14 ) | ( thresh & 0xFFF )
    ctx.obj.exec(f"write {su736_dis_base+0x08} {value}")


#this command wasn't used, but it exists just in case

@trdbox.command()
@click.argument('conf', callback=lambda c,p,x: int(x,0))
@click.pass_context
def dis_conf(ctx, conf):
    ctx.obj.exec(f"write {su736_dis_base+0x0d} {conf}")


#this command basically just does reg-write but specifically for pre-conf
#we ran out of time this year so we couldn't separate this command into
#multiple commands, one for external triggers, one for LUT value, etc.

@trdbox.command()
@click.argument('val', callback=lambda c,p,x: int(x,0))
@click.pass_context
def set_pre_conf(ctx,val):
    address = getAddress("pre_conf")
    write(ctx,address,val)


#this command is meant to reset the pre-cnt register, but we couldn't
#ever get it to work unfortunately

@trdbox.command()
@click.pass_context
def reset_pre_cnt(ctx):#resets pre signal counter
    address = getAddress("pre_cnt")
    write(ctx,address,0x00000000)


#this command was also never used, and I don't believe it's functional

@trdbox.command()
@click.argument('val', callback=lambda c,p,x: int(x,0))
@click.pass_context
def set_pre_stat(ctx, val):
    address = getAddress("pre_stat")
    write(ctx,address,val)


#None of these commands were ever used, and I don't believe they should
#be since these registers are meant to give information about the status
#of the TRDBOX and are not necessarily meant to be writable

#@trdbox.command()
#@click.argument('val', callback=lambda c,p,x: int(x,0))
#@click.pass_context
#def set_dis_freq0(ctx,val):
#    address = getAddress("dis_freq0")
#    write(ctx,address,val)
#
#
#@trdbox.command()
#@click.argument('val', callback=lambda c,p,x: int(x,0))
#@click.pass_context
#def set_dis_freq1(ctx,val):
#    address = getAddress("dis_freq1")
#    write(ctx,address,val)
#
#
#@trdbox.command()
#@click.argument('val', callback=lambda c,p,x: int(x,0))
#@click.pass_context
#def set_dis_time0(ctx,val):
#    address = getAddress("dis_time0")
#    write(ctx,address,val)
#
#
#@trdbox.command()
#@click.argument('val', callback=lambda c,p,x: int(x,0))
#@click.pass_context
#def set_dis_time1(ctx,val):
#    address = getAddress("dis_time1")
#    write(ctx,address,val)


#this command sends a software trigger to the TRD chamber

@trdbox.command()
@click.argument('cmd', default=1)
@click.pass_context
def pretrigger(ctx, cmd):
    ctx.obj.exec(f"write 0x08 {cmd}")


#this command tests out the optical links between the TRDBOX
#and TRD chamber

@trdbox.command()
@click.argument('sfp')
@click.argument('cmd')
@click.pass_context
def sfp(ctx, sfp, cmd):
    ctx.obj.exec(f"sfp{sfp} {cmd}")


#this command was supposed to reset a few key registers to reasonable default
#values (reasonable meaning it won't break things), but we couldn't get it
#to work in time

@trdbox.command()
@click.pass_context
def reset(ctx):
#    set_pre_conf(ctx, str(0x0000fe04))
    set_dgg(ctx, 10, 12, 10, 12)
    dis_thr(ctx, 0, 2048)
    dis_thr(ctx, 1, 2048)
#    reset_pre_cnt(ctx)
#    set_pre_stat(ctx, 0x00000000)
#    set_dis_conf(ctx, conf = 0x0000000c)
#    set_dis_freq0(ctx,param = 0x00000000)
#    set_dis_freq1(ctx,param = 0x00000000)
#    set_dis_time0(ctx,param = 0x1d910000)
#    set_dis_time1(ctx,param = 0x8bfe0009)

#this command allows one to read from a specific register,
#but it's not that useful since you can just do trdbox status
#to see all the registers

@trdbox.command()
@click.argument('address', callback=lambda c,p,x: int(x,0))
@click.pass_context
def reg_read(ctx, address):
    rd = int(ctx.obj.exec(f"read {address}"),16)
    print(rd)
    print(f"Read from 0x{address:04x}: {rd} = 0x{rd:08x}")
    return rd


#this command was going to be used internally for more commands,
#but again we ran out of time :(

def read(ctx, address):
    rd = int(ctx.obj.exec(f"read {address}"),16)
    print(f"Read from 0x{address:04x}: {rd} = 0x{rd:08x}")
    return rd

#this command allows you to write data to a specific register,
#where the data is of the form "OxFFFFFFFF"

@trdbox.command()
@click.argument('address', callback=lambda c,p,x: int(x,0))
@click.argument('data', callback=lambda c,p,x: int(x,0))
@click.pass_context
def reg_write(ctx, address, data):
    ctx.obj.exec(f"write {address} {data}")


#this command is used internally only to write values to addresses

def write(ctx, address, data):
    ctx.obj.exec(f"write {address} {data}")

#this command is used internally to get the HEX values of addresses
#when given the name of the address - I question its usefulness but
#here we are

def getAddress(addressName):
    if(addressName == "pre_conf"):return 0x100
    elif(addressName == "pre_dgg"):return 0x101
    elif(addressName == "pre_cnt"):return 0x102
    elif(addressName == "pre_stat"):return 0x103
    elif(addressName == "dis_conf"):return 0x28d
    elif(addressName == "dis_freq0"):return 0x280
    elif(addressName == "dis_freq1"):return 0x281
    elif(addressName == "dis_time0"):return 0x284
    elif(addressName == "dis_time1"):return 0x285
