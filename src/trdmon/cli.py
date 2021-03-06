
# from . import start as start_loop
# from . import start as start_loop

from . import dimwid
from . import trdbox
from . import roc
from . import dim

import logging
import urwid
import os
import pwd



# ===========================================================================

def cli():

    # set up logging to /tmp/trdmon-{username}.log
    username = pwd.getpwuid( os.getuid() )[ 0 ]
    logging.basicConfig(filename='/tmp/trdmon-%s.log' % username,
      level=logging.DEBUG,
      format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
    logger=logging.getLogger(__name__)


    palette = [
        ('state', 'light green', 'black'),

        ('fsm:off',     'dark gray',  'black'),
        ('fsm:static',  'light blue', 'black'),
        ('fsm:ready',   'light green', 'black'),
        ('fsm:trans',   'yellow',     'black'),
        ('fsm:error',   'white',      'light red'),

        ('bg', 'light gray', 'black'),
        ('foo', 'light red', 'black'),
    ]




    top_widget = urwid.Frame(
        header=urwid.Text(("bg", "HEADER")),
        body =
        urwid.AttrMap(urwid.Filler(urwid.Pile([
            urwid.LineBox(trdbox.daq()),
            urwid.LineBox(trdbox.trigger()),
            urwid.LineBox(roc.info(0,2,0)),
            urwid.LineBox(dim.servers()),
        ])), 'bg'),
        focus_part='header')

    # ----------------------------------------------------------------
    # column layout
    # ----------------------------------------------------------------

    # top_widget = urwid.Frame(
    #     header=urwid.Text(("bg", "HEADER")),
    #     body =
    #     urwid.AttrMap(urwid.Filler(urwid.Columns([
    #         # urwid.Pile([
    #             urwid.LineBox(trdbox.daq()),
    #             urwid.LineBox(trdbox.trigger()),
    #         # ]),
    #         # urwid.Pile([
    #             # urwid.LineBox(trdmon.roc.state(0,2,0)),
    #             urwid.LineBox(roc.info(0,2,0)),
    #             urwid.LineBox(dim.servers()),
    #         # ]),
    #         # trdbox_daq2(),
    #         # trdbox_daq_run(),
    #         # trdbox_daq_bytes_read(),
    #     ])), 'bg'),
    #     focus_part='header')


    dimwid.start(top_widget, palette)
