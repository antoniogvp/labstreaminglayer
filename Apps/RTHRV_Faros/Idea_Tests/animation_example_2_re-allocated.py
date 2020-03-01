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

    # Create and start the simulate class process
    simulation = simulate(q)
    # simulate.start()

    # Create the base plot
    # plot(q, window)
    plotting = plot(q)

    # simulate(q)
    # print 'simulate() Done'

    # print 'main() Done'


class plot(multiprocessing.Process):
    # Function to create the base plot.
    # Make sure to make global the lines, axes, canvas and any part that you
    # would want to update later
    def __init__(self, q):
        self.q = q
        multiprocessing.Process.__init__(self)
        # Start:
        self.start()

    def terminate(self):
        self.q.put('Terminate')
        self.window.destroy()
        self.q.close()
        time.sleep(2)
        self.terminate()

    def updateplot(self):
        stopFlag = False
        if (not self.q.empty()):  # Try to check if there is data in the queue
            while (not self.q.empty()):
                result = self.q.get()
                if result == 'Terminate':
                    print "Found termination flag"
                    # window.quit()
                    stopFlag = True

            if (not stopFlag):
                # here get crazy with the plotting, you have access to all
                # the global variables that you defined in the plot function,
                # and have the data that the simulate sent.
                self.line.set_ydata(result)
                self.ax.draw_artist(self.line)
                self.canvas.draw()
                self.window.after(500, self.updateplot)
            else:
                print 'stopFlag True'
                # Check the queue-flushing method:
                if self.q.empty():
                    print "Queue empty at stop."
                else:
                    count = 0
                    while (not self.q.empty()):
                        count += 1
                        self.q.get()
                    print "Queue contains", count, "items at stop."
                self.terminate()
                return
        else:
            self.window.after(500, self.updateplot)

    def run(self):
        # Create a window
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.terminate)
        self.window.configure(bg='black')
        self.window.tk_setPalette(background='#282820',
                                  foreground='black',
                                  activeBackground='black',
                                  activeForeground='grey')

        # global line, ax, canvas
        self.fig = matplotlib.figure.Figure(linewidth=2.0, frameon=False)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        self.t = range(0, 1280, 1)
        # Centreline:
        self.ax.plot(self.t, [1280 / 2, ] * len(self.t),
                     color='white', alpha=0.3, linewidth=2.0)
        # Actual data (starting value):
        self.line, = self.ax.plot(self.t, self.t,
                                  color='#40E0D0', linewidth=2.0)

        # Beautify:
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.set_axis_bgcolor('black')
        self.ax.set_xlabel("Seconds", fontsize=14, color='white', alpha=0.3)
        self.ax.set_xlim(0, 1280)
        self.ax.set_ylim(0, 1280)
        self.ax.set_xticks(range(0, 1281, 256))
        self.ax.set_xticklabels([str(x) for x in range(0, 1281, 256)],
                                fontsize=14, color='white')
        self.ax.set_yticks(range(256, 1281, 256))
        self.ax.set_yticklabels([str(x) for x in range(256, 1281, 256)],
                                fontsize=14, color='white')
        self.ax.tick_params(axis="both", which="both", bottom="off", top="off",
                            labelbottom="on", left="off", right="off",
                            labelleft="on")

        # Run the animation:
        self.updateplot()

        self.window.mainloop()
        print "Window Done"
        self.q.put('Terminate')

        # Check the queue-flushing method:
        if self.q.empty():
            print "Queue empty."
        else:
            count = 0
            while (not self.q.empty()):
                count += 1
                self.q.get()
            print "Queue contains", count, "items."
        return


class simulate(multiprocessing.Process):
    def __init__(self, q):
        self.q = q
        multiprocessing.Process.__init__(self)

        self.exit = multiprocessing.Event()
        self.start()

    def run(self):
        iterations = xrange(40)
        t = range(0, 1280, 1)
        for i in iterations:
            try:
                time.sleep(0.1)
                # here send any data you want to send to the other process,
                # can be any pickable object
                points = []
                for i in t:
                    points.append(random.randint(0, 1280))
                # if random.randint(0, 100) > 95:
                #     q.put('Terminate')
                #     return

                try:
                    print "q.put now..."
                    self.q.put_nowait(points)
                except:
                    print "q.put failed"
                    pass
            except:
                pass
        try:
            self.q.put_nowait('Terminate')  # The "end of program" flag
        except:
            pass
        self.exit.set()

if __name__ == '__main__':
    main()
