# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 14:44:35 2019

@author: Antonio
"""

## CREATE A MATLAB STREAM
## OPEN IN ANOTHER TERMINAL!!

import os.path
import matlab.engine

eng1 = matlab.engine.start_matlab()

eng1.cd("C:\\Users\\Antonio\\Documents\\ISAE-Supaero\\MAE1\\Research_Project\\labstreaminglayer-master\\OnlinePlotter\\MATLABViewer\\liblsl-Matlab\\examples")

eng1.addpath(eng1.genpath("C:\\Users\\Antonio\\Documents\\ISAE-Supaero\\MAE1\\Research_Project\\labstreaminglayer-master\\OnlinePlotter\\MATLABViewer\\liblsl-Matlab"))

eng1.SendData(nargout=0,background=True)