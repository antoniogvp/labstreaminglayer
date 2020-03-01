# -*- coding: utf-8 -*-
#

"""##########################
Function:
        ::::::::::      :::    :::      ::::    :::       ::::::::
        :+:             :+:    :+:      :+:+:   :+:      :+:    :+:
        +:+             +:+    +:+      :+:+:+  +:+      +:+
        :#::+::#        +#+    +:+      +#+ +:+ +#+      +#+
        +#+             +#+    +#+      +#+  +#+#+#      +#+
        #+#             #+#    #+#      #+#   #+#+#      #+#    #+#
        ###              ########       ###    ####       ########
##########################"""


# Update dictionary from given variables (if any):
def parseargv(argDict, argv, helpdescription=None):
    """Updates and returns a dictionary from corresponding command line args.

    * argDict is a dict or OrderedDict (suggested) with entries of the form:
          "longvar", [default_value, "help_tip", "shortvar", "type_text"]
          Types are enforced by type(default_value).
    * To add a flag arg (i.e. one that requires no value), set default_value = None.
          It will be returned as a bool, with True if called, False if not.
    * argv comes from sys.argv[1:]
    * helpdescription is the description string to display in the
          help text"""

    import sys, getopt, inspect, os.path
    from collections import OrderedDict

    # caller ID:
    caller = inspect.stack()[1][1]  # File path of calling script
    caller = os.path.basename(caller) # extract filename

    # Define a help entry:
    # This is a bit clumsy, but it works, and we're not in a hurry anyway:
    argDict2 = OrderedDict()
    argDict2['help'] = [None, "Display this help text", "h", ""]
    for entry in argDict:
        argDict2[entry] = argDict[entry]
    argDict = argDict2.copy()
    del argDict2

    # Pull out the short vars with ":" only for those with associated data:
    argString = "".join([var[2] + (var[0] != None) * ":" for var in argDict.values()])
    # Pull out the long vars with "=" only for those with associated data:
    argList = [string + (argDict[string][0] != None) * '=' for string in argDict.keys()]

    # Get widths of columns for the help string:
    wLong = 4  # min
    wDefault = 5  # min
    wType = 5  # min
    for longvar in argDict:
        wLong = max(wLong, len(longvar))
        wDefault = max(wDefault, len(str(argDict[longvar][0])))
        wType = max(wType, len(argDict[longvar][3]))

    # Create the printable list of those vars for the help string
    varsString = ""
    for longvar in argDict:
        shortvar = argDict[longvar][2]
        default = argDict[longvar][0]
        # isString = isinstance(default, str)
        # default = isString * "\"" + str(default) + isString * "\""
        default = str(default)
        typetext = argDict[longvar][3]
        tip = argDict[longvar][1]
        varsString += ("--" + longvar.ljust(2 + wLong) +
                       " [-" + (shortvar + "] ").rjust(3) +
                       ((default != 'None') * default + " ").rjust(1 + wDefault +1) +
                       str((typetext != '')*(" (" + typetext + ")")).ljust(1 + wType + 1 + 1) +
                       " : " + tip + "\n")
    helpString = ("\n--------------------------------------------------------------"
                  "\n" + caller.replace(".py","").replace("_", " ") +
                  "\n--------------------------------------------------------------" +
                  (helpdescription!=None) * ("\n    " + helpdescription) +
                  "\n\nUsage:"
                  "\n\n    " + caller + " -x <val> --xlong <val>"
                                        "\n\nPermissible args and values:"
                                        "\n--------------------------------------------------------------"
                                        "\n" + "  long".ljust(2 + wLong + 1) + " " +  # width of longvar column
                  "short" + " " +  # width of shortvar column
                  "default".rjust(1 + wDefault + 1) + " " +  # width of default column
                  "type".ljust(1 + wType + 1 + 1) +  # width of type column
                  "\n" +
                  "-"*(2 + wLong + 1) + " " +  # width of longvar column
                  "-"*(5) + " " +  # width of shortvar column
                  "-"*(1 + wDefault + 1) + " " +  # width of default column
                  "-"*(1 + wType + 1 + 1) +  # width of type column
                  "\n" + varsString +
                  "--------------------------------------------------------------")

    errorString = ("\nError:"
                   "\nLive Plotting Process usage:"
                   "\n    LivePlotting_Process_Commandline.py --var <val1> -v <val2> --flag -f"
                   "\n    --help or -h for help and type")
    typeErrorString = ("Value/Type Error:"
                       "\n    --help or -h for help")
    argErrorString = ("Unexpected Argument Error:"
                       "\n    --help or -h for help")


    # # Delete any NoneType entries
    # # (so only those that are given in the commandline will be returned):
    # for longvar in argDict:
    #     if argDict[longvar][0] is None:
    #         # print longvar
    #         del argDict[longvar]

    # Try to extract the commandline arguments:
    try:
        opts, args = getopt.getopt(argv, argString, argList)
    except getopt.GetoptError:
        print errorString
        sys.exit(2)

    # Check for unexpected args:
    if args != []:
        print "\nUnexpected arg(s):", ' '.join(args)
        print errorString[1:] # no linebreak
        sys.exit(2)

    # If successful, parse them:
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print helpString
            sys.exit()
        else:
            for entry in argDict:
                if opt in ("--" + entry, "-" + argDict[entry][2]):
                    # print "--" + entry, "-" + argDict[entry][2]
                    if type(argDict[entry][0]) is bool:
                        if arg == "True":
                            argDict[entry][0] = True
                            # print "found bool"
                        elif arg == "False":
                            argDict[entry][0] = False
                            # print "found bool"
                        else:
                            print "\nFor", opt, arg
                            print typeErrorString
                            sys.exit(2)
                    elif type(argDict[entry][0]) is int:
                        try:
                            argDict[entry][0] = int(arg)
                            # print "found int"
                            # print argDict[entry][0]
                        except ValueError:
                            print "\nFor", opt, arg
                            print typeErrorString
                            sys.exit(2)
                    elif type(argDict[entry][0]) is float:
                        try:
                            argDict[entry][0] = float(arg)
                            # print "found float"
                            # print argDict[entry][0]
                        except ValueError:
                            print "\nFor", opt, arg
                            print typeErrorString
                            sys.exit(2)
                    elif type(argDict[entry][0]) is type(None):
                        try:
                            argDict[entry][0] = True
                            # print "found flag"
                            # print argDict[entry][0]
                        except ValueError:
                            print "\nFor", opt, arg
                            print typeErrorString
                            sys.exit(2)
                    else: # assume string
                        try:
                            argDict[entry][0] = arg
                            # print "found string"
                        except ValueError:
                            print "\nFor", opt, arg
                            print typeErrorString
                            sys.exit(2)

    # Return False for any un-called flag variables (i.e. with default = None)
    for entry in argDict:
        if type(argDict[entry][0]) is type(None):
            argDict[entry][0] = False
    # i.e. All flag variables will return True if called and False if not.

    # Remove 'help' entry before returning
    del argDict['help']

    return argDict


"""##########################
Main:
        ::::    ::::           :::          :::::::::::      ::::    :::
        +:+:+: :+:+:+        :+: :+:            :+:          :+:+:   :+:
        +:+ +:+:+ +:+       +:+   +:+           +:+          :+:+:+  +:+
        +#+  +:+  +#+      +#++:++#++:          +#+          +#+ +:+ +#+
        +#+       +#+      +#+     +#+          +#+          +#+  +#+#+#
        #+#       #+#      #+#     #+#          #+#          #+#   #+#+#
        ###       ###      ###     ###      ###########      ###    ####
##########################"""

###################################################################
if __name__ == "__main__":
    """Runs this if not called from another script"""

    import sys
    from collections import OrderedDict

    # Entry format: (longvar, [default, tip, shortvar, typetext])
    argDict = OrderedDict([
            ("random",
             [None, "Test variable", "b", ""]),
            ("plot_rate",
             [15, "Refresh rate for plot", "p", "int"]),
            ("rate",
             [500, "Expected data rate (ignored if no internalTime)", "r", "int"]),
            ("windowTime",
             [5, "Width of t-axis (seconds)", "w", "int"]),
            ("type",
             ["ECG", "LSL stream type label to look for", "T", "str"]),
            ("internalTime",
             [True, "Use internally generated timestamps rather than received ones", "i", "bool"]),
            ("thickness",
             [2.0, "Line thickness", "t", "float"]),
            ("col",
             ["gold", "Colour: one of: 'gold', 'red', 'blue', 'gray/grey', or 'silver'", "c", "str"]),
            ("negative",
             [True, "Negate values", "n", "bool"]),
            ("inverted",
             [False, "Take the inverse (e.g. for rate from frequency)", "N", "bool"]),
            ("scale",
             [1.0, "Multiplies y-values by this (after inverse)", "s", "float"]),
            ("offset",
             [0.0, "Add to reading (before inversion or scaling)", "o", "float"]),
            ("valueText",
             ["", "Text, if desired, to indicate the current value (e.g. 'BPM' for heart-rate)", "v", "str"]),
                        ])

    helpdescription = "Plots a 1-channel numeric stream from Lab Streaming Layer"
    argDict = parseargv(argDict, sys.argv[1:], helpdescription=helpdescription)

    print "\nProcessed commandline args:"
    varsString = ""
    for longvar in argDict:
        shortvar = argDict[longvar][2]
        default = argDict[longvar][0]
        isString = isinstance(default, str)
        default = isString * "\"" + str(default) + isString * "\""
        tip = argDict[longvar][1]
        varsString += ("--" + longvar.ljust(14) +
                       " [-" + (shortvar + "] ").rjust(3) +
                       str((default != 'None') * default).rjust(7) +
                       " : " + tip + "\n")
    print "\n", varsString

# print argList
# print argString.translate(None, ':')
# for i, arg in enumerate(argList):
#     print arg.translate(None, '='), argString.translate(None, ':')[i]