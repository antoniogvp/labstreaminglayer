# python 2.7.11
###############################################################################
# Configuration GUI function

"""
Contains a function that:
Launches a GUI pop-up for selecting/inputting configuration data.
Saves these variables, correctly cast, to an external "Config.py" file.
Also first loads default values from that file if it already exists
so that subsequent runs do not need to re-type the values. Returns a
dictionary of the variables, but suggested usage is:
>>> from ConfigGUI import ConfigGUI
>>> ConfigGUI(title, message)
>>> from Config import *

Launched with no options, this with read the entire Config file if one exists
and exit() if such a file does not exist.
Options:
title
message
readOnly = If this is True, this function just returns the selected
           variables and does not display the GUI to allow the user to
           edit the values. Defaults to False (show GUI).
setToDefaults = like readOnly, but ignores the contents of the Config file
                and writes the default values given in the dictionary.
descWidth = wrap width of description field in *pixels*
            (this field is used for, e.g. units).
entryWidth = width of entry field in *characters*. Defaults to the length
             of an IP.
configDict = a specific DICTIONARY OF VARIABLES you want to configure.
    * If this is specified, will load and modify only those variables
    * If these variables to not exist in the Config file, will add them
    * To add a description (e.g. a unit), define the values in this
      dictionary as (value, description) or [value, description]
    * Descriptions will be wrapped to descWidth and all field heights
      updated accordingly. Newlines and whitespace in descriptions will
      be ignored.

*A TRICK:
readOnly and setToDefault can be used as read() and write() functions if
you want to  substitue your own GUI (for browsing for a file path, for
example):
>>> from ConfigGUI import ConfigGUI

>>> ConfigGUI(configDict={"filePath": ""}, readOnly=True)
>>> from Config import *

>>> filePath = yourGUIBrowserPathSomethingFunction(filePath)

>>> # Now set your modified variable as the "default":
>>> ConfigGUI(configDict={"filePath": filePath}, setToDefaults=True)
>>> from Config import *
"""
###############################################################################

"""
General flow concept:
1. Set "default" variables
2. If Config file exists, load values.
3. Launch GUI with fields for each requested variable.
4. Save fields to file.
5. Return variables.
Main
6. Run script within this file.
"""


def ConfigGUI(title="Config",
              message="Edit Config file values here:",
              configDict={}, descWidth=0, entryWidth=len("000.000.000.000"),
              readOnly=False, setToDefaults=False):
    """Launches a GUI pop-up for selecting/inputting configuration data.
    Saves these variables, correctly cast, to an external "Config.py" file.
    Also first loads default values from that file if it already exists
    so that subsequent runs do not need to re-type the values. Returns a
    dictionary of the variables, but suggested usage is:
    >>> from ConfigGUI import ConfigGUI
    >>> ConfigGUI(title, message)
    >>> from Config import *

    Options:
    title (Window title bar)
    message (Title/message within the window)
    readOnly = If this is True, this function just returns the selected
               variables and does not display the GUI to allow the user to
               edit the values. Defaults to False (show GUI).
    setToDefaults = like readOnly, but ignores the contents of the Config file
                    and writes the default values given in the dictionary.
    descWidth = wrap width of description field in *pixels*
                (this field is used for, e.g. units).
    entryWidth = width of entry field in *characters*. Defaults to the length
                 of an IP.
    configDict = a specific DICTIONARY OF VARIABLES you want to configure.
        * If this is specified, will load and modify only those variables
        * If these variables to not exist in the Config file, will add them
        * To add a description (e.g. a unit), define the values in this
          dictionary as (value, description) or [value, description]
        * Descriptions will be wrapped to descWidth and all field heights
          updated accordingly. Newlines and whitespace in descriptions will
          be ignored.

    *A TRICK:
    readOnly and setToDefault can be used as read() and write() functions if
    you want to  substitue your own GUI (for browsing for a file path, for
    example):
    >>> from ConfigGUI import ConfigGUI

    >>> ConfigGUI(configDict={"filePath": ""}, readOnly=True)
    >>> from Config import *

    >>> filePath = yourGUIBrowserPathSomethingFunction(filePath)

    >>> # Now set your modified variable as the "default":
    >>> ConfigGUI(configDict={"filePath": filePath}, setToDefaults=True)
    >>> from Config import *
    """

    import os.path
    import Tkinter as tk
    import time

    """Local Variabes"""
    # Create a flag to indicate whether we are creating a new file,
    # in which case we need to give the OS time to create and write
    # before we can use (import) the file:
    creatingFileFlag = False
    # Similarly create a flag for for writing new variables as this
    # also takes a little extra time:
    newVariableFlag = False
    writeString = ("# \"" + "Config.py" + "\"\n" +
                   "# - config file for ConfigGUI.py\n\n"
                   "# This is Python, therefore this is a comment\n\n"
                   "# NOTE: variable names cannot start with '__'\n\n")
    # bigInstructions = title + "\n\n" + message
    bigInstructions = message
    # bigInstructions = ("Network Setup:\n\nEnter network and ECG parameters:")
    smallInstructions = ("\"Okay\"/<Enter> to accept.\n"
                         "\"Defaults\" to revert to script defaults.\n"
                         "\"Reset\" to undo changes (incl. "
                         "\"Defaults\").\n"
                         "<Esc>/Close window to reset and close.")

    """
    ###########################################################################
    # Initialise        ###   ##   #   ###   #####
    #                    #    # #  #    #      #
    #                    #    #  # #    #      #
    #                    #    #   ##    #      #
    #                   ###   #    #   ###     #
    ###########################################################################
    """

    # If no dictionary specified, read the entire config file:
    if configDict == {}:
        if os.path.exists("Config.py"):
            print ("No dictionary given, Config.py file found.\n"
                   "Loading full Config file...")
            # It's a Python file, so just import:
            import Config
            for var in dir(Config):
                if not var.startswith("__"):
                    configDict[var] = getattr(Config, var)
        else:
            print ("No dictionary given and no Config.py file found.\n"
                   "Aborting.")
            exit()

    # Create a values-only dictionary, and format the original one:
    # (If there is a description, extract only element 0 from the
    #  tuple. Wrap the description strings. Then, if there is no
    #  description, update the Full dictionary with a blank
    #  description for the GUI.)
    valuesDict = {}
    for entry in configDict:
        if type(configDict[entry]) is tuple or \
                type(configDict[entry]) is list:  # If description given:
                    # if it's a tuple, make it a list:
                    configDict[entry] = list(configDict[entry])
                    valuesDict[entry] = configDict[entry][0]
                    # Wrap strings:
                    string = configDict[entry][1]

                    string = string.replace("\r\n", " ")
                    string = " ".join(string.split())
                    # string = \
                    #     textwrap.fill(string, width=descWidth)

                    configDict[entry][1] = string
        else:  # If there is no description
            valuesDict[entry] = configDict[entry]
            # Add a blank one (for the GUI):
            configDict[entry] = (configDict[entry], "")

    # Create a shallow copy of the main dictionary before the Config
    # file is read, for use by the "defaults" button:
    configDictDefault = valuesDict.copy()

    """
    ###########################################################################
    # Functions         #####   #   #   ##   #    ####
    #                   #        # #    # #  #   #
    #                   ####      #     #  # #    ###
    #                   #        # #    #   ##       #
    #                   #       #   #   #    #   ####
    ###########################################################################
    """

    # Function for booleans as strings (from a dictionary):
    def castBool2String(valuesDict, varName):
        """Casts a boolean to a string (from a dictionary).
        Returns the cast value only and does not modify the original.
        Therefore usage:
        >>> targetDict[varName] = castString(valuesDict, varName)"""
        if valuesDict[varName] is True:
            return "True"
        elif valuesDict[varName] is False:
            return "False"
        else:
            # return the original
            return valuesDict[varName]

    # Function for intelligently casting a string (from a dictionary):
    def castString(valuesDict, varName):
        """Casts a string from a dictionary. Interprets "True" and "False" as
        Booleans. Returns the cast value only. Does not modify the original.
        Therefore usage:
        >>> targetDict[varName] = castString(valuesDict, varName)"""
        # First reinterpret boolean strings:
        if valuesDict[varName] == "True":
            return True
        elif valuesDict[varName] == "False":
            return False
        elif type(valuesDict[varName]) is bool:
            # Leave it alone if it already is a boolean
            return bool(valuesDict[varName])
        else:
            try:
                return int(valuesDict[varName])
                # Booleans won't be cast to 1/0 because we've already
                # checked them and left them alone in the previous elif
            except ValueError:
                try:
                    return float(valuesDict[varName])
                except ValueError:
                    # Must be string:
                    return str(valuesDict[varName])

    # Function for appending a new line to a writeString variable:
    def append(name, var, writeString):
        """
        Takes a variable name and its value and appends lines to the
        writeString in the format:
        name = "var" (if string)
        or
        name = var (if other type)

        Intended use: writeString = append(name, dict[name], writeString)
        """
        if type(var) is str:  # needs quotation marks
            writeString = writeString + name + " = \"" + str(var) + "\"\n"
        else:  # Assume float or int, therefore needs no quotation marks
            writeString = writeString + name + " = " + str(var) + "\n"
        return writeString

    """
    ###########################################################################
    # Classes           ####   #        #     ####   ####  #####   ####
    #                  #    #  #       # #   #      #      #      #
    #                  #       #      #   #   ###    ###   #####   ###
    #                  #    #  #      #####      #      #  #          #
    #                   ####   #####  #   #  ####   ####   #####  ####
    ###########################################################################
    """

    """########################################################################
    # ROOT WINDOW:
    ########################################################################"""

    class root(tk.Tk):
        def __init__(self, master=None):
            tk.Tk.__init__(self, master, className="\n" + title)
            # Hide the window until it is properly sized and positioned:
            self.withdraw()
            # Catch the Windows exit window command ("Red X" button):
            self.protocol("WM_DELETE_WINDOW", self.closer)
            # And then start:
            self.createFrames()

        def createFrames(self):
            # Window instructions:
            self.instrBigLabel = tk.Label(self, text=bigInstructions,
                                          justify="left", anchor="n",
                                          font=('Helvetica', 10),
                                          bd=10)
            self.instrBigLabel.pack(side="top", fill=tk.Y,
                                    anchor="nw")

            # Add entry frames:
            for varName in sorted(configDicttemp, reverse=True):
                Entry = varEntry(master=self)

                # NAME and DESCRIPTION
                Entry.varName.set(varName)  # Name label
                Entry.varDesc.set(configDict[varName][1])  # Description

                # VALUE ENTRY:
                # Cast Booleans as strings, not 0/1:
                configDicttemp[varName] = \
                    castBool2String(configDicttemp, varName)
                # Put the value into the entry box:
                Entry.varVal.set(configDicttemp[varName])
                # Justify strings/booleans to the right for easier reading:
                try:
                    int(configDicttemp[varName])
                except ValueError:
                    try:
                        float(configDicttemp[varName])
                    except ValueError:  # Assume string
                        Entry.valEntry.config(justify="right")

                # INTELLIGENT FORMATTING:
                # Italicise tiemout variables to highlight them:
                if "timeout" in varName or "Timeout" in varName:
                    Entry.nameLabel.config(font=('Helvetica', 10,
                                                 "italic"))
                # Highlight port-number entries:
                if "port" in varName or "Port" in varName:
                    Entry.valEntry.config(font=('Helvetica', 10,
                                                "bold"))
                # Highlight boolean entries:
                if configDicttemp[varName] == "True" or \
                        configDicttemp[varName] == "False":
                    Entry.valEntry.config(font=('Helvetica', 10,
                                                "bold"))
                Entry.pack(anchor="w")

            self.instrSmallLabel = tk.Label(self, text=smallInstructions,
                                            justify="left", anchor="n",
                                            font=('Helvetica', 7),
                                            fg="gray50",
                                            bd=10)
            self.instrSmallLabel.pack(side="top", fill=tk.Y,
                                      anchor="nw")

            # Add the other widgets (buttons):
            self.createWidgets()

        def createWidgets(self):
            # Okay button:
            self.OKAY = tk.Button(self, text="Okay",
                                  command=self.okayButton)
            # Bind the "Return" key to the OKAY button
            self.bind('<Return>', (lambda ret,
                                   b=self.OKAY: self.OKAY.invoke()))

            # Reset button:
            self.RESET = tk.Button(self, text="Reset",
                                   command=self.resetButton)
            # Bind the "Escape" key to the exit with the Reset command
            self.bind('<Escape>', (lambda esc,
                                   b=self.RESET: self.closer()))

            # Defaults button:
            self.DEFAULTS = tk.Button(self, text="Defaults",
                                      relief="flat",
                                      fg="grey50",
                                      command=self.defaultsButton)

            # Packing order:
            self.OKAY.pack(side="right")
            self.RESET.pack(side="right")
            self.DEFAULTS.pack(side="left")

            # Position in the centre of the screen:
            # "Draw" window (even if it is still withdrawn)
            self.update()
            w = self.winfo_width()  # width for the Tk root
            h = self.winfo_height()  # height for the Tk root
            # get screen width and height
            ws = self.winfo_screenwidth()  # width of the screen
            hs = self.winfo_screenheight()  # height of the screen
            # calculate centre x and y coordinates
            x = (ws / 2) - (w / 2)
            y = (hs / 2) - (h / 2)
            # set the dimensions of the window and where it is placed
            self.geometry("%dx%d+%d+%d" % (w, h, x, y))
            self.minsize(width=w, height=h)
            self.maxsize(width=w, height=h)
            # Finally, re-show the window, now that it is sized and positioned
            self.deiconify()

        def okayButton(self):
            self.destroy()

        def defaultsButton(self):
            for entry in configDicttemp:
                # Reset values:
                configDicttemp[entry] = configDictDefault[entry]
            self.resetFrame()

        def resetButton(self):
            for entry in configDicttemp:
                # Reset values:
                configDicttemp[entry] = valuesDict[entry]
            self.resetFrame()

        def resetFrame(self):
            for item in self.winfo_children():
                item.destroy()
            self.createFrames()

        def closer(self):
            print "\n##===============================================##" + \
                  "\n|| Warning:                                      ||" + \
                  "\n|| Window closed without user accepting changes. ||" + \
                  "\n|| Resetting values...                           ||" + \
                  "\n##===============================================##\n"
            for entry in configDicttemp:
                # Reset values:
                configDicttemp[entry] = valuesDict[entry]
            # # Cast:
            # for varName in configDicttemp:
            #     configDicttemp[varName] = castString(configDicttemp, varName)
            # And quit:
            self.destroy()

    """########################################################################
    # ENTRY ROWS FOR EACH VARIABLE:
    ########################################################################"""

    class varEntry(tk.Frame):
        def __init__(self, master=None):
            tk.Frame.__init__(self, master)
            self.myparent = master
            self.pack(side="top")
            self.createWidgets()

        def createWidgets(self):
            # variable name as label on left:
            self.varName = tk.StringVar()

            self.nameLabel = tk.Label(self, font=('Helvetica', 10,
                                                  ""),
                                      width=labelWidth, anchor="w")
            self.nameLabel["textvariable"] = self.varName

            # variable value as entry on right:
            self.varVal = tk.StringVar()
            self.valEntry = tk.Entry(self, width=entryWidth,
                                     font=('Helvetica', 10))
            self.valEntry["textvariable"] = self.varVal
            self.varVal.trace("w", self.traceEntry)

            # variable description as text on far right:
            self.varDesc = tk.StringVar()
            self.Desc = tk.Label(self, font=('Helvetica', 8, ""),
                                 anchor="w", justify="left",
                                 wraplength=descWidth, fg="grey50",
                                 relief="flat")
            self.Desc["textvariable"] = self.varDesc

            # Packing order:
            self.Desc.pack(side="right", anchor="nw")
            self.valEntry.pack(side="right", anchor="nw")
            self.nameLabel.pack(side="left", anchor="nw")

        def traceEntry(self, n, m, x):
            # FYI: "x" is the acces mode, incase it's needed later...
            # "w"=write, "r"=read, "u"=undefined (variable deleted)
            # print self.varVal.get()
            configDicttemp[self.varName.get()] = self.varVal.get()
            return

    """
    ###########################################################################
    # Main              #     #     #     ###   ##   #
    #                   ##   ##    # #     #    # #  #
    #                   # # # #   #   #    #    #  # #
    #                   #  #  #   #####    #    #   ##
    #                   #     #   #   #   ###   #    #
    ###########################################################################
    """

    """########################################################################
    # READ Config FILE
    ########################################################################"""
    if os.path.exists("Config.py"):
        # print "Config file found"
        # It's a Python file, so just import:
        import Config
        # Now look for the required values in the config file.
        # Config file can be sparse (be missing some values), but it will
        # be repopulated after *this* script runs.
        for imported in dir(Config):
            if not imported.startswith("__"):
                for original in valuesDict.keys():
                    if original == imported and not setToDefaults:
                        # Update valuesDicts for every value found in the
                        # Config file, but only if setToDefaults is False:
                        valuesDict[original] = getattr(Config,
                                                       imported)
        # Now check if there any new values that do not yet exist in the file:
        for original in valuesDict.keys():
            notFoundFlag = True
            for imported in dir(Config):
                if not imported.startswith("__"):
                    if original == imported:
                        notFoundFlag = False
            # if notFoundFlag returns True, the variable was not found in the
            # file, so we have a new variable:
            newVariableFlag = newVariableFlag or notFoundFlag

    else:
        print "No config file found; creating new one with default values."
        creatingFileFlag = True

    """########################################################################
    # GUI
    ########################################################################"""
    if not (readOnly or setToDefaults):
        # Create "shallow" copy for editing while GUI is running
        configDicttemp = valuesDict.copy()
        labelWidth = 1
        # Set label width to fit longest label:
        for entry in configDicttemp:
            labelWidth = max(labelWidth, len(entry))
        # Launch GUI:
        root = root()
        # Maintain GUI until closed:
        root.mainloop()
        # Update valuesDict:
        valuesDict = configDicttemp

    """########################################################################
    # CAST and OVERWRITE Config FILE
    ########################################################################"""

    # Cast strings from entry fields:
    # Function for casting strings received from entry fields:

    # Cast type for every entry in the valuesDict dictionary:
    for varName in valuesDict:
        valuesDict[varName] = castString(valuesDict, varName)

    # Create a dictionary for all Config file variables and updates
    # i.e. everything that will be written to the file:
    fileDict = {}
    # First load all the variables in the file (if it exists):
    if os.path.exists("Config.py"):
        for var in sorted(dir(Config)):
            if not var.startswith("__"):
                fileDict[var] = getattr(Config, var)
    # Then update to the values from this function:
    for varToChange in valuesDict.keys():
            fileDict[varToChange] = valuesDict[varToChange]

    # Now create the writeString, in alphabetical order:
    for var in sorted(fileDict.keys()):
        # print var
        writeString = append(var, fileDict[var], writeString)
    # print writeString

    # Finally, overwrite the config file with the complete writeString:
    ConfigFile = open("Config.py", "w")  # open to overwrite
    # print "file open for writing"
    ConfigFile.write(writeString)
    ConfigFile.close()

    # If creating a new file, give the OS time to write:
    if newVariableFlag and (not creatingFileFlag):
        print "Adding new variable(s) to file..."
        time.sleep(1.5)
    if creatingFileFlag:
        print "Creating new Config file..."
        time.sleep(1.5)

    # Load the new file, then, if it already existed and was loaded
    # earlier (in which case "import Config" does nothing),
    # Reload the updated Config.py "module" in case we have added
    # anything new.
    import Config
    reload(Config)

    """########################################################################
    # RETURN
    ########################################################################"""
    return valuesDict

# The following only runs if this script is run on its own for testing,
# not if called as a function from another script.
if __name__ == "__main__":
    debugDict = {
                 "ignoreTCP": (True, """Ignore creating a TCP
                                         connection (quicker)."""),
                 "askConfirm": (True, """Ask user to confirm the start
                                          of each major step"""),
                 "askSend": (True, "Ask user to initiate sending the data"),
                 "debugPrinter": (True, "Print verbose status messages"),
                 "valDebugPrinter": (False, "Print sent values"),
                 "hexDebugPrinter": (False, """Print actual encoded
                                               packets"""),
                 "simpleSTOP": (False, """Do not animate the STOP button
                                          (for slower PCs, perhaps)"""),
                 }

    testDict = {
                "rate": (256, "Hz"),
                # "example_variable": True,  # can be any type
                "TCP_Host": "localhost",
                "TCP_Port": 1000,
                "TCPtimeout": (1, "sec"),
                "UDP_ClientIP": "localhost",
                "UDP_ClientPort": 1001,
                "UDP_ServerIP": "localhost",
                "UDP_ServerPort": 1003,
                "UDPtimeout": [1, "sec"]
                }
    title = "Network Setup"
    message = "Enter network and ECG parameters:"
    # print ConfigGUI("Debug options:", "Select run parameters:",
    #                 configDict=debugDict, descWidth=160, entryWidth=5)
    print ConfigGUI(title, message, configDict=testDict, descWidth=40)
    # print ConfigGUI(readOnly=True)
    # print ConfigGUI()
    # print ConfigGUI(configDict=debugDict, setToDefaults=True)

    # import os.path
    # while not os.path.exists("Config.py"):
    #     print "waiting..."
    #     time.sleep(0.1)

    from Config import *

    # print "rate           ", rate, "Hz", type(rate)
    # print "TCP_Port       ", TCP_Port, type(TCP_Port)
    # print "TCP_Host       ", TCP_Host, type(TCP_Host)
    # print "TCPtimeout     ", TCPtimeout, type(TCPtimeout)
    # print "UDP_ClientIP   ", UDP_ClientIP, type(UDP_ClientIP)
    # print "UDP_ClientPort ", UDP_ClientPort, type(UDP_ClientPort)
    # print "UDP_ServerIP   ", UDP_ServerIP, type(UDP_ServerIP)
    # print "UDP_ServerPort ", UDP_ServerPort, type(UDP_ServerPort)
    # print "UDPtimeout     ", UDPtimeout, type(UDPtimeout)
