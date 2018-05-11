# -*- coding: utf-8 -*-
"""
Created on Tue May  1 14:39:50 2018

@author: Steff
"""

import sys
sys.path.insert(0, ".\..\data")

from AbstractsModel import AbstractsModel
from DataLoader import DataLoader
import pandas as pd

filename = "abstracts.train.pkl"

d = DataLoader()
if not d.get_persistent(filename):
    d.papers(["2013","2014","2015"]).abstracts().conferences()
    d.data = d.data[["chapter","chapter_abstract","conference","conference_name"]].copy()
    d.data.drop(
        list(d.data[pd.isnull(d.data.chapter_abstract)].index),
        inplace=True
    )
    d.make_persistent(filename)

model = AbstractsModel()
model.train(d.data[0:20000])
#model.print_top_k(10)


test = model.query_single("Hello there, what is going on have some data for me dude please vector")
print(test)