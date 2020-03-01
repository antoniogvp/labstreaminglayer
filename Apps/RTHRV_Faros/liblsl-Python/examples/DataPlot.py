# from: http://pyqwt.sourceforge.net/gui-examples.html
# The Python version of Qwt-5.0.0/examples/data_plot

# for debugging, requires: python configure.py  --trace ...
if False:
    import sip
    sip.settracemask(0x3f)

import random
import sys

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *
import time
from PyQt4 import QtGui, QtCore


class DataPlot(Qwt.QwtPlot):
    def __init__(self, titlePlot="noTitleSet", legendCurveOne="noLegendSet",legendCurveTwo=None,*args):#, *args
        Qwt.QwtPlot.__init__(self,*args)#, *args
        #print "TOTO:"+str(*args)
        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()
        
        # Initialize data
        #self.x = arange(0.0, 100.1, 0.5)
        self.x = arange(0.0, 500.1, 0.5)
        
        self.y = zeros(len(self.x), Float)
        self.z = zeros(len(self.x), Float)
        
        self.setTitle(titlePlot)
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)
        
        self.curveOne = Qwt.QwtPlotCurve(legendCurveOne)
        self.curveOne.attach(self)

        

        self.setMarker(50,"Welcome\n")
        
        #self.startTimer(50)
        self.phase = 0.0
        self.isAnalysed = False
        
        self.legendCurveTwo = legendCurveTwo
        if not legendCurveTwo==None: #and not self.isAnalysed:
            self.curveTwo = Qwt.QwtPlotCurve(legendCurveTwo)
            self.curveTwo.attach(self)
        
        #to add yellow circles
        #if not legendCurveTwo==None:
        #    self.curveTwo.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
        #                                Qt.QBrush(),
        #                                Qt.QPen(Qt.Qt.yellow),
        #                                Qt.QSize(7, 7)))

        self.curveOne.setPen(Qt.QPen(Qt.Qt.red))
        if not legendCurveTwo==None:
            self.curveTwo.setPen(Qt.QPen(Qt.Qt.blue))
        
        mY = Qwt.QwtPlotMarker()
        mY.setLabelAlignment(Qt.Qt.AlignRight | Qt.Qt.AlignTop)
        mY.setLineStyle(Qwt.QwtPlotMarker.HLine)
        mY.setYValue(0.0)
        mY.attach(self)
        
        self.setAxisTitle(Qwt.QwtPlot.xBottom, "Time (s)")
        self.setAxisTitle(Qwt.QwtPlot.yLeft, "Value [C]")
        

        
        #self.setAxisScale(0,-1,1)
    # __init__()
    
    def addStateMACDCurve(self):
        self.isAnalysed = True
        self.s = zeros(len(self.x), Float)
        self.curveState = Qwt.QwtPlotCurve("(MACD - Signal)")
        self.curveState.attach(self)
        self.curveState.setPen(Qt.QPen(Qt.Qt.darkRed))
        
    def setStateMACD(self,val):
        self.s = concatenate((self.s[1:], self.s[:1]), 1)
        self.s[-1]=val    
        
        #if val>0:
        #    self.curveState.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
        #                                Qt.QBrush(),
        #                                Qt.QPen(Qt.Qt.yellow),
        #                                Qt.QSize(7, 7)))        
        #else:
        #    self.curveState.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
        #                                Qt.QBrush(),
        #                                Qt.QPen(Qt.Qt.green),
        #                                Qt.QSize(7, 7)))                                        

    def alignScales(self):
        #print ""
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)

    # alignScales()

    def timerEvent(self, e):
        if self.phase > pi - 0.0001:
            self.phase = 0.0        
        # y moves from left to right:
        # shift y array right and assign new value y[0]
        self.y = concatenate((self.y[:1], self.y[:-1]), 1)
        self.y[0] = sin(self.phase) * (-1.0 + 2.0*random.random())
        
        # z moves from right to left:
        # Shift z array left and assign new value to z[n-1].
        self.z = concatenate((self.z[1:], self.z[:1]), 1)
        self.z[-1] = 0.8 - (2.0 * self.phase/pi) + 0.4*random.random()
        
        self.curveOne.setData(self.x, self.y)
        #self.curveTwo.setData(self.x, self.z)
        
        self.replot()
        self.phase += pi*0.02

    def oneShotTest(self):
        if self.phase > pi - 0.0001:
            self.phase = 0.0

        # y moves from left to right:
        # shift y array right and assign new value y[0]
        self.y = concatenate((self.y[:1], self.y[:-1]), 1)
        self.y[0] = sin(self.phase) * (-1.0 + 2.0*random.random())
        
        # z moves from right to left:
        # Shift z array left and assign new value to z[n-1].
        self.z = concatenate((self.z[1:], self.z[:1]), 1)
        self.z[-1] = 0.8 - (2.0 * self.phase/pi) + 0.4*random.random()

        self.curveOne.setData(self.x, self.y)
        self.curveTwo.setData(self.x, self.z)

        self.replot()
        self.phase += pi*0.02


        
    def initGraph(self,firstValX,firstValY,winLen=100,xStep=0.5):
        self.winLen = winLen
        self.xStep = xStep
        self.firstValX = firstValX
        self.x = arange(firstValX-winLen, firstValX,xStep)
        self.y = zeros(len(self.x), Float)
        self.z = zeros(len(self.x), Float)
        self.s = zeros(len(self.x), Float)
        #self.dataAppend(firstValX,firstValY)
        

    def dataAppend(self,valX,valY):
        # Shift x array left and assign new value to x[-1].
        self.x = concatenate((self.x[1:], self.x[:1]), 1)
        self.x[-1]=valX
        # Shift y array left and assign new value to y[-1].
        self.y = concatenate((self.y[1:], self.y[:1]), 1)
        self.y[-1]=valY
        #refresh plot
        self.curveOne.setData(self.x, self.y)
        self.setAxisScale(2,self.x[0],self.x[-1],self.xStep*50)
        #self.setAxisScale(2,self.x[0],self.x[-1],self.xStep)
        self.replot()
    # timerEvent()
    
    def dataAppendTwoCurves(self,valX,valY,valZ):
        # Shift x array left and assign new value to x[-1].
        self.x = concatenate((self.x[1:], self.x[:1]), 1)
        self.x[-1]=valX
        # Shift y array left and assign new value to y[-1].
        self.y = concatenate((self.y[1:], self.y[:1]), 1)
        self.y[-1]=valY
        
        self.z = concatenate((self.z[1:], self.z[:1]), 1)
        self.z[-1]=valZ
        
        #refresh plot
        self.curveOne.setData(self.x, self.y)
        if not self.legendCurveTwo==None and not self.isAnalysed:
            self.curveTwo.setData(self.x, self.z)
        if self.isAnalysed:
            self.curveState.setData(self.x, self.s)        
        self.setAxisScale(2,self.x[0],self.x[-1],self.xStep*50)
        #self.setAxisScale(2,self.x[0],self.x[-1],self.xStep)
        self.replot()

    def setMarker(self,xPos,title):
        marker = Qwt.QwtPlotMarker()
        marker.setLabel(Qwt.QwtText(title))
        marker.setItemAttribute(Qwt.QwtPlotItem.AutoScale, True)
        marker.setLineStyle(Qwt.QwtPlotMarker.VLine)
        marker.setXValue(xPos) 
        marker.setLabelAlignment(QtCore.Qt.AlignRight)
        marker.attach(self)


# class DataPlot
'''
def make():
    demo = DataPlot()
    demo.resize(500, 300)
    demo.show()
    return demo

# make()

def main(args): 
    app = Qt.QApplication(args)
    demo = make()
    sys.exit(app.exec_())

# main()

# Admire
if __name__ == '__main__':
    main(sys.argv)
'''
# Local Variables: ***
# mode: python ***
# End: ***

if __name__ == '__main__':
    args=sys.argv
    app = Qt.QApplication(args)
    demo = DataPlot()
    demo.resize(500, 300)
    demo.show()
    onlyDemo=False
    if onlyDemo:
        demo.startTimer(50)
        #for i in range(0,100):
        #    demo.oneShotTest()
    else:
        demo.initGraph(0,0,20,0.5)
        for i in range(0,200):
            #demo.dataAppend(i,math.sin(i))
            if i<50:
                demo.dataAppend(i,i*i)
            else:
                demo.dataAppend(i,25000-i*i)
            print i
            time.sleep(0.01)
            #raw_input("press a key")


	

    sys.exit(app.exec_())


