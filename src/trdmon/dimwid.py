#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dimwid
"""

# import sys
# import time
# import curses
import urwid
# import proc
# import dimmon
import pydim
# import trdbox
import logging
# import json
import os
import struct
# from pprint import pprint
# import functools

def exit_on_enter(key):
    if key=='enter' or key=='q':
        raise urwid.ExitMainLoop()

def start(top_widget, palette):
    loop = urwid.MainLoop(top_widget, palette, unhandled_input=exit_on_enter)
    dimwid.connect_loop(loop)

    loop.run()


class dimwid_t:

    def __init__(self):
        self.callbacks = dict()
        self.pipefd = None

    def register_callback(self, cb):
        self.callbacks[id(cb)] = cb
        # print(self.callbacks.keys())
        # logger.debug(f"registering {id(cb)}")

    def request_callback(self, cb):
        if self.pipefd is not None:
            os.write(self.pipefd, struct.pack("Q", id(cb)))

    def receive_output(self, x):
        for id in struct.iter_unpack("Q", x):
            self.callbacks[id[0]].refresh()

    def connect_loop(self, loop):
        self.pipefd = loop.watch_pipe(self.receive_output)

dimwid = dimwid_t()
