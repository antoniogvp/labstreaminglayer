# -*- coding: utf-8 -*-
###############################################################################
# A basic nameEntry.Entry GUI function
###############################################################################
import time
import Tkinter as tk


def nameEntry(message="", default=""):
    """nameEntry.Entry-field window. Returns the field.

    Default value optional."""

    def nameEntryCloser():
        nameEntry.field.set(default)
        nameEntry.nameWindow.quit()

    def okayButton():
        nameEntry.nameWindow.quit()
        return

    # WINDOW:
    nameEntry.nameWindow = tk.Tk(className=" Provide Identifier")
    nameEntry.nameWindow.protocol("WM_DELETE_WINDOW", nameEntryCloser)
    # Hide until positioned:
    nameEntry.nameWindow.withdraw()

    # VARIABLES :
    nameEntry.field = tk.StringVar()
    nameEntry.field.set(default)

    # Widgets:
    nameEntry.EntryFrame = tk.Frame(nameEntry.nameWindow)
    nameEntry.ButtonFrame = tk.Frame(nameEntry.nameWindow)

    nameEntry.Label = tk.Label(nameEntry.EntryFrame, text=message)
    nameEntry.Entry = tk.Entry(nameEntry.EntryFrame, width=15,
                               textvariable=nameEntry.field)

    nameEntry.OKAY = tk.Button(nameEntry.ButtonFrame, text="Okay",
                               command=okayButton, width=8)
    nameEntry.CANCEL = tk.Button(nameEntry.ButtonFrame, text="Cancel",
                                 command=nameEntryCloser, width=8)

    nameEntry.nameWindow.bind('<Escape>', (lambda esc,
                                           b=nameEntry.CANCEL:
                                           nameEntry.CANCEL.invoke()))
    nameEntry.nameWindow.bind('<Return>', (lambda ret,
                                           b=nameEntry.OKAY:
                                           nameEntry.OKAY.invoke()))

    # Pack:
    nameEntry.EntryFrame.pack(fill="x")
    nameEntry.ButtonFrame.pack(fill="x")
    nameEntry.Label.pack(side="left", anchor="nw")
    nameEntry.Entry.pack(side="right", anchor="nw")
    nameEntry.CANCEL.pack(side="right", anchor="se", fill="x")
    nameEntry.OKAY.pack(side="right", anchor="se")

    # Position in the centre of the screen:
    # "Draw" window (even if it is still withdrawn)
    nameEntry.nameWindow.update()
    w = nameEntry.nameWindow.winfo_width()  # width for the Tk root
    h = nameEntry.nameWindow.winfo_height()  # height for the Tk root
    # get screen width and height
    ws = nameEntry.nameWindow.winfo_screenwidth()  # width of the screen
    hs = nameEntry.nameWindow.winfo_screenheight()  # height of the screen
    # calculate centre x and y coordinates
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    # set the dimensions of the window and where it is placed
    nameEntry.nameWindow.geometry("%dx%d+%d+%d" % (w, h, x, y))
    nameEntry.nameWindow.minsize(width=w, height=h)
    nameEntry.nameWindow.maxsize(width=w, height=h)
    # Finally, re-show the window, now that it is sized and positioned
    nameEntry.nameWindow.deiconify()

    # Hold until quit:
    nameEntry.nameWindow.mainloop()
    # Once nameEntry.nameWindow has been quit,
    # return what was in the entry field:
    return nameEntry.field.get()


print "Returned \"" + nameEntry(message="Enter an ID for the run:",
                                default="This") + "\""
