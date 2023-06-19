import os
import platform
import logging
import numpy

cbstate = ""

scale_percent = 100


rotation = -1   

if platform.system() == "Windows":
    windowsos = True
    mydir = r"C:\Users\bharg\OneDrive\Desktop\chessrobot\images" + "\\"
    stockfishexe = r"C:\Users\bharg\Downloads\stockfish_14_win_x64\stockfish_14_win_x64\stockfish_14_x64.exe"
    cameraportno = 1
   
    cameratype = 'usb'
    #cameratype = 'ip'
    serialport = "COM7"    
else:
    windowsos = False
   
    mydir = "images/"
    cameraportno = 0
    serialport = '/dev/ttyACM0'
    
    
motorsareservos = False
SCARA = True

stockfishparams={"Threads": 4}

logging.basicConfig(level=logging.DEBUG, filename = mydir + 'chesslog.log', filemode='w', format='%(levelname)s-%(message)s')
kingincheck = False

fisheye = False

DIM=(1280, 720)
K=numpy.array([[817.2563502237226, 0.0, 623.8797454131019], [0.0, 817.8633343903235, 383.3817964461323], [0.0, 0.0, 1.0]])
D=numpy.array([[-0.15014017025387882], [1.3554015587876163], [-11.583862737184841], [29.439951469529348]])

fisheyeimages = "fishimages/"