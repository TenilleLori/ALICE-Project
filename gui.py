from tkinter import *
from tkinter.ttk import *
from functools import partial
import zmq
from zmq import ssh

class inputGUI(Tk):

    argsEntry = None
    tempInput = ""

    def __init__(self, caption, command, tempInput):
        super().__init__()
        self.title("Add Input to " + caption.get())

        frame = Frame(self)
        frame.grid()

        self.tempInput = tempInput

        Label(frame, text="Add args to " + str(command) + ":").grid(row=0, column=0)
        self.argsEntry = Entry(frame)
        self.argsEntry.grid(row=0, column=1)

        Button(frame, text="Add Command", command=self.add).grid(row=1, column=0)
        Button(frame, text="Cancel", command=self.cancel).grid(row=1, column=1)

    def add(self):
        self.tempInput.set(self.argsEntry.get())
        self.destroy()
    
    def cancel(self):
        self.destroy()


class configGUI(Tk):

    btnNum = 0

    btnCaptions = None
    btnCommands = None
    commandEntry = None
    captionEntry = None
    inputCheckbox = None
    i = 0

    def __init__(self, btnNum, btnCaptions, btnCommands):
        super().__init__()
        self.title("Configure Button " + str(btnNum+1))

        self.btnNum = btnNum
        self.btnCaptions = btnCaptions
        self.btnCommands = btnCommands

        self.i = IntVar()
        
        frame = Frame(self)
        frame.grid()

        Label(frame, text="Enter New Button Caption").grid(row=0, column=0)
        self.captionEntry = Entry(frame)
        self.captionEntry.grid(row=0, column=1)
        
        Label(frame, text="Enter New Button Command").grid(row=1, column=0)
        self.commandEntry = Entry(frame)
        self.commandEntry.grid(row=1, column=1)

        self.inputCheckbox = Checkbutton(frame, text="Require Input for this Command?", variable=self.i)
        self.inputCheckbox.grid(row=2, column=0, columnspan=2)

        Button(frame, text="Save", command=self.save).grid(row=3, column=0)
        Button(frame, text="Cancel", command=self.cancel).grid(row=3, column=1)

    def save(self):
        self.btnCaptions[self.btnNum].set(self.captionEntry.get())
        self.btnCommands[self.btnNum] = [self.commandEntry.get(), self.i.get()]
        self.destroy()

    def cancel(self):
        self.destroy()



class mainGUI(Tk):

    numBtns = 5
    actnBtns = []
    confBtns = []
    btnCaptions = []
    btnCommands = []
    addedCommands = []
    tempInput = ""

    socket = None

    frame = None
    entry = None
    text = None
    addBtn = None
    remBtn = None
    exeBtn = None

    def __init__(self, socket):
        super().__init__()

        self.socket = socket
        self.tempInput = StringVar()

        self.title("TRD Control GUI")

        self.frame = Frame(self)
        self.frame.grid()

        for i in range(self.numBtns):
            self.btnCaptions.append(StringVar(self.frame, "Function " + str(i+1)))
            self.btnCommands.append("")

            actnPart = partial(self.btnAction, i)
            self.actnBtns.append(Button(self.frame, textvariable=self.btnCaptions[i], command=actnPart))
            self.actnBtns[i].grid(row=i, column=0)

            confPart = partial(self.configure, i)
            self.confBtns.append(Button(self.frame, text="Configure", command=confPart))
            self.confBtns[i].grid(row=i, column=1)

        self.addBtn = Button(self.frame, text="Add Button", command=self.newBtn)
        self.addBtn.grid(row=self.numBtns, column=0)
        self.remBtn = Button(self.frame, text="Remove Button", command=self.popBtn)
        self.remBtn.grid(row=self.numBtns, column=1)

        self.entry = Entry(self.frame)
        self.entry.grid(row=0, column=2, columnspan=2)
        btnAddCustom = Button(self.frame, text="Add Custom Command", command=self.btnCustom)
        btnAddCustom.grid(row=0, column=4)

        self.text = Text(self.frame)
        self.text.grid(row=1, column=2, rowspan=self.numBtns, columnspan=3)

        self.exeBtn = Button(self.frame, text="Execute Command Sequence", command=self.execute)
        self.exeBtn.grid(row=self.numBtns+1, column=2)

    def newBtn(self):
        self.numBtns += 1

        self.btnCaptions.append(StringVar(self.frame, "Function " + str(self.numBtns)))
        self.btnCommands.append("")

        actnPart = partial(self.btnAction, self.numBtns-1)
        self.actnBtns.append(Button(self.frame, textvariable=self.btnCaptions[self.numBtns-1], command=actnPart))
        self.actnBtns[self.numBtns-1].grid(row=self.numBtns-1, column=0)

        confPart = partial(self.configure, self.numBtns-1)
        self.confBtns.append(Button(self.frame, text="Configure", command=confPart))
        self.confBtns[self.numBtns-1].grid(row=self.numBtns-1, column=1)

        self.addBtn.grid(row=self.numBtns, column=0)
        self.remBtn.grid(row=self.numBtns, column=1)
        self.text.grid(row=1, column=2, rowspan=self.numBtns, columnspan=3)
        self.exeBtn.grid(row=self.numBtns+1, column=2)

    def popBtn(self):
        self.numBtns -= 1
        self.actnBtns[self.numBtns].destroy()
        self.actnBtns.pop(self.numBtns)
        self.confBtns[self.numBtns].destroy()
        self.confBtns.pop(self.numBtns)
        self.addBtn.grid(row=self.numBtns, column=0)
        self.remBtn.grid(row=self.numBtns, column=1)
        self.text.grid(row=1, column=2, rowspan=self.numBtns, columnspan=3)
        self.exeBtn.grid(row=self.numBtns+1, column=2)

    def btnAction(self, btnNum):
        if self.btnCommands[btnNum] == "":
            return

        if self.btnCommands[btnNum][1] == 0:
            argsGUI = inputGUI(self.btnCaptions[btnNum], self.btnCommands[btnNum][0], self.tempInput)
            argsGUI.wait_window(argsGUI)
            self.addedCommands.append(self.btnCommands[btnNum][0] + " " + self.tempInput.get())
            self.updateText()
        
        else:
            self.addedCommands.append(self.btnCommands[btnNum])
            self.updateText()

    def configure(self, btnNum):
        confScreen = configGUI(btnNum, self.btnCaptions, self.btnCommands)

    def btnCustom(self):
        self.addedCommands.append(self.entry.get())
        self.updateText()

    def updateText(self):
        self.text.delete("1.0", END)
        for i in range(len(self.addedCommands)):
            self.text.insert(INSERT, self.addedCommands[i] + "\n")

    def execute(self):
        for i in range(len(self.addedCommands)):
            self.socket.send_string(self.addedCommands[i])
            print(self.socket.recv())

if __name__=="__main__":
    ctx = zmq.Context()
    sock = ctx.socket(zmq.REQ)
    ssh.tunnel_connection(sock, "tcp://localhost:7766", "trd@alicetrd.phy.uct.ac.za")
    app = mainGUI(sock)
    app.mainloop()