import threading


class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)

def someFunc():
    print "someFunc was called"

# Example usage
def someOtherFunc(data, key):
    print "someOtherFunc was called : data=%s; key=%s" % (str(data), str(key))


t1 = threading.Thread(target=someFunc)
t1.start()
t1.join()


t1 = FuncThread(someOtherFunc, [1, 2], 6)
t1.start()
t1.join()