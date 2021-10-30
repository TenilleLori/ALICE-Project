##IMPORTANT - This GUI runs locally - there is no need to run the GUI on the server, it'll probably still work but its unnecessary
##          - You do need to enter your TRD computer SSH password to run this, comment out the ssh.tunnel_connection in the main method to test the GUI without making changes to the server

from tkinter import * #the GUI interface used to make the GUI
from tkinter.ttk import * #replaces some of the components with more modern-looking ones (i.e. the buttons)
from functools import partial #used to make sure the buttons act on the correct commands
import zmq #used to set up the socket connection
from zmq import ssh #used to connect the socket to the TRD computer

class inputGUI(Tk): ##The GUI used to get input from the user when commands are set to run with custom input

    argsEntry = None    #The component where the input is written in, is a class variable as it is referenced in multiple methods
    tempInput = ""  #The input string - is set to the string passed to it of the same name, therefore it changes the one in mainGUI (Python is pass by reference)

    def __init__(self, caption, command, tempInput):
        super().__init__()
        self.title("Add Input to " + caption.get())

        frame = Frame(self)
        frame.grid()    #The Grid layout is used so it's the same as the mainGUI
        
        self.tempInput = tempInput #Changes to self.tempInput will now change tempInput in mainGUI - pass by reference

        Label(frame, text="Add args to " + str(command) + ":").grid(row=0, column=0)
        self.argsEntry = Entry(frame)
        self.argsEntry.grid(row=0, column=1) #Done in a separate line, as .grid() returns None, so then argsEntry isn't saved to be used later, the rest aren't used later so they can be created and positioned at once

        Button(frame, text="Add Command", command=self.add).grid(row=1, column=0)
        Button(frame, text="Cancel", command=self.cancel).grid(row=1, column=1)

    def add(self):
        self.tempInput.set(self.argsEntry.get())
        self.destroy()
    
    def cancel(self):   #Not done in-line as this would destroy this GUI on initialisation for some reason
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

    #I'm not sure if all the Nones need to be declared and initialised outside of __init__, it might just be a leftover of my Java background - feel free to remove these if it still works

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
    rmvEntry = None
    rmvBtn = None
    exeBtn = None

    def __init__(self, socket):
        super().__init__()

        self.socket = socket    #The socket is passed so that the GUI can make changes to server without having to pass everything back to the main method
        self.tempInput = StringVar()    #StringVar is a special data type associated with Tkinter, which dynamically updates displays using it if it is changed

        self.title("TRD Control GUI")

        self.frame = Frame(self)    #The basis component
        self.frame.grid()   #All components which are called upon are created and placed in different lines, otherwise its variable is set to None

        for i in range(self.numBtns):   #Creates the action and config buttons - Action buttons execute whatever action they are configured to do by its corresponding config buttons
            self.btnCaptions.append(StringVar(self.frame, "Function " + str(i+1))) #Each button's caption is defined by a StringVar, as config can change the caption
            self.btnCommands.append("") #Each buttons command is initially blank, but needs to be initialised as this can cause errors otherwise

            actnPart = partial(self.btnAction, i)   #The partial binds the current value of i as the input of the function, since otherwise each button would simply execute the last button (button numBtns)
            self.actnBtns.append(Button(self.frame, textvariable=self.btnCaptions[i], command=actnPart)) #textvariable is used instead of text for StringVars
            self.actnBtns[i].grid(row=i, column=0)

            confPart = partial(self.configure, i)
            self.confBtns.append(Button(self.frame, text="Configure", command=confPart)) #As the caption doesn't change, the text argument is used
            self.confBtns[i].grid(row=i, column=1)

        self.entry = Entry(self.frame)  #Used to add a custom command that can be entered without having to set up a button for it - good for once-offs
        self.entry.grid(row=0, column=2, columnspan=2)
        btnAddCustom = Button(self.frame, text="Add Custom Command", command=self.btnCustom).grid(row=0, column=4)

        self.addBtn = Button(self.frame, text="Add Button", command=self.newBtn)    #Used to add a new pair of action and config buttons
        self.remBtn = Button(self.frame, text="Remove Button", command=self.popBtn) #Used to remove the last pair of buttons - could use input screen to choose which buttons to remove maybe

        self.text = Text(self.frame, state=DISABLED) #Displays the current command sequence - is set to be disabled as the user cannot write on this screen to change the commands, so it might be a bit weird if they can type on it anyway
        self.exeBtn = Button(self.frame, text="Execute Command Sequence", command=self.execute) #Passes the command sequence to the server and clears the command sequence 

        self.rmvEntry = Entry(self.frame)   #Used to specify which command should be removed from the sequence
        self.rmvBtn = Button(self.frame, text="Remove Command", command=self.remove)    #Removes the given command from the sequence

        self.align()    #Aligns the components whose alignment depends on the amount of buttons - as there are many methods that change numBtns, its simpler do always use the same method for it

    def newBtn(self):   #Adds a new pair of action and config buttons - essentially a single loop through the part of __init__ where the first of these buttons are initialised - maybe rewrite these into a new function? 
        self.numBtns += 1   

        self.btnCaptions.append(StringVar(self.frame, "Function " + str(self.numBtns)))
        self.btnCommands.append("")

        actnPart = partial(self.btnAction, self.numBtns-1)
        self.actnBtns.append(Button(self.frame, textvariable=self.btnCaptions[self.numBtns-1], command=actnPart))
        self.actnBtns[self.numBtns-1].grid(row=self.numBtns-1, column=0)

        confPart = partial(self.configure, self.numBtns-1)
        self.confBtns.append(Button(self.frame, text="Configure", command=confPart))
        self.confBtns[self.numBtns-1].grid(row=self.numBtns-1, column=1)

        self.align()     #Realigns some components as numBtns changed

    def popBtn(self):    #Removes the last set of buttons from the screen - could be changed to allow user to specify which pair to remove 
        self.numBtns -= 1
        self.actnBtns[self.numBtns].destroy()
        self.actnBtns.pop(self.numBtns) #pop removes the item at the specified index from the array, and shortens the array by 1
        self.confBtns[self.numBtns].destroy()
        self.confBtns.pop(self.numBtns)
        self.align()

    def btnAction(self, btnNum):    #Is executed when Button number btnNum is pressed

    #The commands are stored in an array as this is much easier to do than bind the actual command to each button

        if self.btnCommands[btnNum] == "":  #Does nothing if no command is set
            return

        if self.btnCommands[btnNum][1] == 0:    #Runs if command is set to ask for input
            argsGUI = inputGUI(self.btnCaptions[btnNum], self.btnCommands[btnNum][0], self.tempInput)
            argsGUI.wait_window(argsGUI)    #Waits until argsGUI is closed, otherwise tempInput would just be an empty string as the input would be added immediately after the GUI is opened
            self.addedCommands.append(self.btnCommands[btnNum][0] + " " + self.tempInput.get())
            self.updateText()
        
        else:   #Runs if no input is needed
            self.addedCommands.append(self.btnCommands[btnNum])
            self.updateText()

    def configure(self, btnNum): #Sets the command and caption of each action button and whether it requires input
        confScreen = configGUI(btnNum, self.btnCaptions, self.btnCommands)

    def btnCustom(self):    #Adds the custom command to the command sequence
        self.addedCommands.append(self.entry.get())
        self.updateText()

    def updateText(self):   #Writes the current command sequence to the text component
        self.text.config(state=NORMAL)  #The text component must be enabled to be able to write to it
        self.text.delete("1.0", END) #Clears the text on the component
        for i in range(len(self.addedCommands)):
            self.text.insert(INSERT, str(i+1) + ": " + self.addedCommands[i] + "\n")    #The command number is shown to allow the user to easily identify the command number if they want to remove it
        self.text.config(state=DISABLED)

    def align(self):    #Realigns components if needed
        self.addBtn.grid(row=self.numBtns, column=0)
        self.remBtn.grid(row=self.numBtns, column=1)
        self.text.grid(row=1, column=2, rowspan=self.numBtns, columnspan=3)
        self.rmvEntry.grid(row=self.numBtns+1, column=2, columnspan=2)
        self.rmvBtn.grid(row=self.numBtns+1, column=4)
        self.exeBtn.grid(row=self.numBtns+2, column=2, columnspan=2)

    def execute(self):  #Sends commands to the server
        for i in range(len(self.addedCommands)):
            self.socket.send_string(self.addedCommands[i])  #Sends the commands one at a time
        self.addedCommands = [] #Clears the command sequence

    def remove(self):   #Removes the specified command from the command sequence
        cmdNum = int(self.rmvEntry.get())
        self.addedCommands.pop(cmdNum-1)
        self.updateText()

if __name__=="__main__":    #Runs if 'py gui.py' is run from the cmd
    ctx = zmq.Context() #Not entirely sure what this does, but its necessary
    sock = ctx.socket(zmq.REQ)  #Sets up the socket
    ssh.tunnel_connection(sock, "tcp://localhost:7766", "trd@alicetrd.phy.uct.ac.za")   #Connects the socket to the server via SSH, requires passwords
    app = mainGUI(sock) #Creates mainGUI
    app.mainloop()  #Runs the GUI over and over, otherwise the GUI closes a millisecond or so after startup