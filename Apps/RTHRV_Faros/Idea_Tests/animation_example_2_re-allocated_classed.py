import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import multiprocessing
import time
import random
from Tkinter import *
matplotlib.use('TkAgg')


def main():
    # Create a queue to share data between process
    q = multiprocessing.Queue()

    # Create and start the simulation process
    simulate = multiprocessing.Process(None, simulation, args=(q,))
    simulate.start()

    # Create the base plot
    # plot(q, window)
    plotting = multiprocessing.Process(None, plot, args=(q,))
    plotting.start()

    # simulation(q)
    # print 'simulation() Done'

    # print 'main() Done'


def plot(q):
    # Function to create the base plot.
    # Make sure to make global the lines, axes, canvas and any part that you
    # would want to update later

    # Create a window
    window = Tk()
    window.configure(bg='black')
    window.tk_setPalette(background='#282820', foreground='black',
                         activeBackground='black', activeForeground='grey')

    def updateplot(q, window):
        stopFlag = False
        if (not q.empty()):       # Try to check if there is data in the queue
            while (not q.empty()):
                result = q.get()
                if result == 'Terminate':
                    print "Found termination flag"
                    # window.quit()
                    stopFlag = True

            if (not stopFlag):
                # here get crazy with the plotting, you have access to all
                # the global variables that you defined in the plot function,
                # and have the data that the simulation sent.
                line.set_ydata(result)
                ax.draw_artist(line)
                canvas.draw()
                window.after(500, updateplot, q, window)
            else:
                print 'stopFlag True'
                # Check the queue-flushing method:
                if q.empty():
                    print "Queue empty at stop."
                else:
                    count = 0
                    while (not q.empty()):
                        count += 1
                        q.get()
                    print "Queue contains", count, "items at stop."
                return
        else:
            window.after(500, updateplot, q, window)

    # def plotCloser():
    #     q.put('Terminate')
    #     window.quit()
    #     window.destroy()

    # window.protocol("WM_DELETE_WINDOW", plotCloser)

    global line, ax, canvas
    fig = matplotlib.figure.Figure(linewidth=2.0, frameon=False)
    ax = fig.add_subplot(1, 1, 1)
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.show()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
    t = range(0, 1280, 1)
    # Centreline:
    ax.plot(t, [1280 / 2, ] * len(t), color='white', alpha=0.3, linewidth=2.0)
    # Actual data (starting value):
    line, = ax.plot(t, t, color='#40E0D0', linewidth=2.0)

    # Beautify:
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_axis_bgcolor('black')
    ax.set_xlabel("Seconds", fontsize=14, color='white', alpha=0.3)
    ax.set_xlim(0, 1280)
    ax.set_ylim(0, 1280)
    ax.set_xticks(range(0, 1281, 256))
    ax.set_xticklabels([str(x) for x in range(0, 1281, 256)],
                       fontsize=14, color='white')
    ax.set_yticks(range(256, 1281, 256))
    ax.set_yticklabels([str(x) for x in range(256, 1281, 256)],
                       fontsize=14, color='white')
    ax.tick_params(axis="both", which="both", bottom="off", top="off",
                   labelbottom="on", left="off", right="off", labelleft="on")

    updateplot(q, window)
    window.mainloop()
    print "Window Done"
    q.put('Terminate')

    # Check the queue-flushing method:
    if q.empty():
        print "Queue empty."
    else:
        count = 0
        while (not q.empty()):
            count += 1
            q.get()
        print "Queue contains", count, "items."
    return


def simulation(q):
    iterations = xrange(40)
    for i in iterations:
        time.sleep(0.1)
        # here send any data you want to send to the other process,
        # can be any pickable object
        t = range(0, 1280, 1)
        points = []
        for i in t:
            points.append(random.randint(0, 1280))
        # if random.randint(0, 100) > 95:
        #     q.put('Terminate')
        #     return

        q.put(points)
    q.put('Terminate')  # The "end of program" flag for the other process.

if __name__ == '__main__':
    main()
