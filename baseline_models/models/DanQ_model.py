#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 14:06:32 2020

@author: amadeu
"""

import csv

import torch.nn as nn
import torch.nn.functional as F

import numpy as np
from collections import Counter
from argparse import Namespace
import pandas as pd

import numpy as np 
import pandas as pd 
import os
import math


from numpy import array
import torch
import gc
from tqdm import tqdm_notebook as tqdm
from torch.utils.data import Dataset,DataLoader

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')




class NN_class(nn.Module):
    def __init__(self, num_classes, batch_size, seq_size, task):
        super(NN_class,self).__init__()
        self.num_classes = num_classes
        self.num_motifs = 320
        self.batch_size = batch_size
        self.conv1d = nn.Conv1d(4, self.num_motifs, kernel_size=26, stride=1) # with seq_len= 1000 kernel_size=26; seq_len=150 kernelsize=9
        self.seq_size = seq_size
        
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool1d(kernel_size = 13, stride = 13) # seq_len=1000 kernel_size= 13 stride=13; seq_len=150 kernelsize=4 stride=4
        self.dropout = nn.Dropout(p=0.2)
            
        self.lstm = nn.LSTM(self.num_motifs, #
                            self.num_motifs,
                            bidirectional=True)
       
        
        aux_num = (((seq_size-26)+1)-13)/13+1
        self.dropout_2 = nn.Dropout(p=0.5)
        self.num_neurons = math.floor(aux_num)
        self.fc1 = nn.Linear(self.num_motifs*2*self.num_neurons,925) # seq_len 1000 75neuronen; seq_len 150 35neuronen
        self.fc2 = nn.Linear(925, num_classes)
        
        if task == "TF_bindings":
            
            self.final = nn.Sigmoid()
            
        else:
            
            self.final = nn.Identity()
            
        # x = final(x)
        # self.fc2 = nn.Linear(925, num_classes)

    
    def zero_state(self, batch_size):
        return (torch.zeros(2, batch_size, self.num_motifs).to(device),
               torch.zeros(2, batch_size, self.num_motifs).to(device))
        
    
    def forward(self, x, batch_size):
        
      
        x = self.conv1d(x) 
        
        x = self.relu(x)
       
        x = self.maxpool(x)
        
        x = self.dropout(x)
        
        h_0, c_0 = self.zero_state(batch_size)
        #print(x.shape) # [2,320,75]

        
        # x = torch.transpose(x, 1, 2)
        x = x.permute(2,0,1)


        #CNN expects [batchsize, input_channels, signal_length]
        # lstm expects shape [batchsize, signal_length, number of features]
        # print(x.shape)
        #print(prev_state.shape)

             
        output, state = self.lstm(x, (h_0, c_0))
        
        # x = torch.transpose(x, 1, 2)
        #print(x.shape) # [75,2,320]
        x = output.permute(1,0,2)
        #print(x.shape) # [2,75,640]
        
        x = torch.flatten(x, start_dim= 1) 
        x = self.dropout_2(x)


        #x = torch.reshape(output, (self.batch_size,self.num_neurons*self.num_motifs)) # seqlen=1000 75 neuronen; seq_len=150 35 neuronen
        #x = torch.flatten(x,1)

      
        x = self.fc1(x)
      
        x = self.relu(x)
        
        x = self.fc2(x)
        
        x = self.final(x)
        
        return x #, state
    
    


#device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#model = DanQ(num_classes, num_motifs, batch_size).to(device)
#model = DanQ()

#criterion = nn.CrossEntropyLoss()
#optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)



#from modelsummary import summary
#model = DanQ(num_classes=4,num_motifs=6)
#x=torch.zeros((2,4,10))
#state_h = torch.zeros((1,2,6))# für jeden b
#state_c = torch.zeros((1,2,6))
#prev_state = state_h, state_c
#print(summary(model, x, prev_state, show_input=False)) # other output shapes than keras summary, as we receive lstm hiddenstate output instead of lstm output




