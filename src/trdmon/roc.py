
import urwid
import pydim
import logging
from trdmon.dimwid import dimwid as dimwid

class info(urwid.Pile):
    def __init__(self, sm,stack,layer):

        super().__init__([
        urwid.Text("%02d_%d_%d" % (sm,stack,layer)),
        state(sm,stack,layer) ])


class state(urwid.AttrMap): #(urwid.Text("FOO"),"state")):

    def __init__(self, sm,stack,layer):
        self.textwidget = urwid.Text(("state", "SERVICE 2"))
        super().__init__(self.textwidget, {"state": "state"} )
        # super().__init__(self.textwidget, {"fsm:undef": "fsm:undef"})
        pydim.dic_info_service(f"trd-fee_{sm:02d}_{stack}_{layer}_STATE",
                               "I", self.dimcb, timeout=30)
        dimwid.register_callback(self)
        self.state = -999
        self.statemap = {
          -999: "off",
          0: "off",
          13: "ERROR",
          99: "ERROR",
          5: "STANDBY",
          43: "STDBY_INIT",
          3: "CONFIGURED",
          42: "INITIALIZING",
          44: "CONFIGURING",
          45: "TESTING" }

    def dimcb(self, s):
        self.state = s
        dimwid.request_callback(self)

    def refresh(self):

        if self.state in [ -999, 0]:
            self.textwidget.set_text(("fsm:off", "off"))

        elif self.state in [ 13, 99 ]:
            self.textwidget.set_text(("fsm:error", "ERROR"))

        elif self.state == 5:
            self.textwidget.set_text(("fsm:static", "STANDBY"))

        elif self.state == 43:
            self.textwidget.set_text(("fsm:static", "STANDBY_INIT"))

        elif self.state == 3:
            self.textwidget.set_text(("fsm:ready", "CONFIGURED"))

        elif self.state == 42:
            self.textwidget.set_text(("fsm:trans", "INITIALIZING"))

        elif self.state == 44:
            self.textwidget.set_text(("fsm:trans", "CONFIGURING"))

        elif self.state == 45:
            self.textwidget.set_text(("fsm:trans", "TESTING"))

        else:
            self.textwidget.set_text(("fsm:error", f"state:{state:02X}"))
