import PyQt4
from PyQt4.QtCore import QThread,QObject,SIGNAL
from PyQt4.QtGui import QErrorMessage
import serial, time, sys,copy,struct,crcmod


class BluetoothThread(QThread):
    
    def __init__(self, sbuf, rbuf, parent=None):
        QThread.__init__(self,parent)

        self.sendbuf=sbuf
        self.receivebuf=rbuf
        self.ser=serial.Serial()
        self.runThread=True
        self.databuffer=[]
        self.timer=0

    def send(self):

        if self.ser.isOpen():
            
            while len(self.sendbuf)>0:
                a=self.sendbuf.pop(0)
                    
                data=[]
                
                if a[0]==0:
                    if len(a)!=5:
                        continue
                    data.append(chr(0x00))
                    for i in range(1,5):
                        data+=struct.pack('f', a[i])
                else:
                    if len(a)!=16:
                        continue
                    data.append(chr(0xFF))
                    for i in range(1,5):
                        data+=chr(a[i])
                        
                crc = crcmod.Crc(0x1D5, initCrc=0, rev=False)
                crc.update(str(data))
                crc_byte = crc.crcValue
                        
                data+=[chr(crc_byte),'\n']
              
                for d in data:
                    self.ser.write(d)
                    #time.sleep(0.05)

    def initialize(self,port):
        self.runThread=True
        ok=True
        while ok:
            try:
                self.ser = serial.Serial(port)
                ok=False
            except:
                continue
                
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        self.ser.parity = serial.PARITY_NONE #set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        self.ser.timeout = 0          #block read
        self.ser.xonxoff = False     #disable software flow control
        self.ser.rtscts = False     #disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
        self.ser.writeTimeout = 0     #timeout for write

        self.ser.close()
        while not self.ser.isOpen():
            try:
                self.ser.close()
                self.ser.open()
                self.start()
            except Exception, e:
                print "error open serial port: " + str(e)


    def run(self):
        while self.runThread:
            
            a=self.ser.read() 
            if not a:
                continue

            self.databuffer.append(a)
            
            if len(self.databuffer)<22:
                continue
            
            if self.databuffer[0]=='U' and self.databuffer[1]=='U':
                
                helper=time.time()
                if helper-self.timer>0.04:
                    self.timer=helper
                else:
                    self.databuffer=[]
                    continue
                    
                self.databuffer=self.databuffer[2:]
                for i in range(len(self.databuffer)):
                    self.receivebuf.append(self.databuffer.pop(0))
                
                self.emit(SIGNAL("Post()"))
            else:
                self.databuffer.pop(0)
            
        self.ser.close()

    def stop(self):
        self.runThread=False