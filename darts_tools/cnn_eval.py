#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 09:57:51 2021

@author: amadeu
"""

import torch
import torch.nn as nn
# from operations import *
from generalNAS_tools.operations_14_9 import *

from torch.autograd import Variable
from generalNAS_tools.utils import drop_path


# genotype, C_prev_prev, C_prev, C_curr, reduction, reduction_prev


class CNN_Cell_eval(nn.Module):

  def __init__(self, genotype, C_prev_prev, C_prev, C, reduction, reduction_prev):
    super(CNN_Cell_eval, self).__init__()
    self.reduction = reduction

    if reduction_prev:
      self.preprocess0 = FactorizedReduce(C_prev_prev, C)
    else:
      self.preprocess0 = ReLUConvBN(C_prev_prev, C, 1, 1, 0)
    self.preprocess1 = ReLUConvBN(C_prev, C, 1, 1, 0)
    
    # receive the operations from genotype
    if reduction:
      ## meine Version ##
      geno_reduce = genotype[2]
      # geno_reduce = hb_results[0]
      op_names = []
      for op_name in geno_reduce:
          op_names.append(op_name[0])
      indices = []
      for idx in geno_reduce:
          indices.append(idx[1])
      concat = genotype[3]
     
    else:
        
      geno_normal = genotype[0]
      # geno_reduce = hb_results[0]
      op_names = []
      for op_name in geno_normal:
          op_names.append(op_name[0])
      indices = []
      for idx in geno_normal:
          indices.append(idx[1])
      concat = genotype[1]
      
    # C, reduction = 8, False
    self._compile(C, op_names, indices, concat, reduction)

  # in order to receive "_ops" object, with all 8 operations 
  def _compile(self, C, op_names, indices, concat, reduction):
    assert len(op_names) == len(indices)
    self._steps = len(op_names) // 2
    self._concat = concat
    self.multiplier = len(concat)

    self._ops = nn.ModuleList()
    for name, index in zip(op_names, indices):
      stride = 2 if reduction and index < 2 else 1
      op = OPS[name](C, stride, True)
      self._ops += [op]
    self._indices = indices

  # s0, s1 = torch.rand(2,8,10), torch.rand(2,8,10)
  #
  def forward(self, s0, s1, drop_prob):
    s0 = self.preprocess0(s0)
    s1 = self.preprocess1(s1)

    states = [s0, s1]
    for i in range(self._steps):
      h1 = states[self._indices[2*i]] # because for 1th Node only need 0th element and 
      h2 = states[self._indices[2*i+1]] # 1th element of states (for 2th Node we need 2th and 3th element of states)
      op1 = self._ops[2*i]
      op2 = self._ops[2*i+1]
      h1 = op1(h1)
      h2 = op2(h2)
      if self.training and drop_prob > 0.:
        if not isinstance(op1, Identity):
          h1 = drop_path(h1, drop_prob)
        if not isinstance(op2, Identity):
          h2 = drop_path(h2, drop_prob)
      s = h1 + h2
      states += [s]
    return torch.cat([states[i] for i in self._concat], dim=1)