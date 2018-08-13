# -*- coding: utf-8 -*-
"""
Created on Wed Aug  8 13:59:18 2018

@author: Andreea
"""

###### Script parameters #######

LSA_TOPICS = 1000
LSA_RANDOM_STATE = 0

TFIDF_MIN_DF = 0
TFIDF_MAX_DF = 1.0
TFIDF_NGRAM = (1,4)
TFIDF_MAX_FEATURES = None

MAX_RECS = 10

TRAINING_DATA = "small"
TRAINING_DATA_CONCAT = True
TEST_DATA = "small"

BATCHSIZE_EVALUATION = 200
PROCESSES_EVALUATION = 3

#################################

import sys
import os
import multiprocessing as mp

sys.path.insert(0, os.path.join(os.getcwd(),".."))
sys.path.insert(0, os.path.join(os.getcwd(),"..","..","data"))
sys.path.insert(0, os.path.join(os.getcwd(),"..","evaluations"))
from LSAUnionAbstractsModel import LSAUnionAbstractsModel

# Generate model (main + child process).

model = LSAUnionAbstractsModel(
            concat=TRAINING_DATA_CONCAT,
            topics=LSA_TOPICS,
            random_state=LSA_RANDOM_STATE,
            min_df=TFIDF_MIN_DF,
            max_df=TFIDF_MAX_DF,
            ngram_range=TFIDF_NGRAM,
            max_features=TFIDF_MAX_FEATURES,
            recs=MAX_RECS
    )

# Method to run in a multiprocessing process.

def evaluate_model(batch):
    result = model.query_batch(batch)
    return result

# Load model in child process.

if __name__ != '__main__':
    #sys.stderr = open("debug-multiprocessing.err."+str(os.getppid())+".txt", "w")
    #sys.stdout = open("debug-multiprocessing.out."+str(os.getppid())+".txt", "w")
    model._load_model(TRAINING_DATA)

# Main script.

if __name__ == '__main__':
    from DataLoader import DataLoader
    import numpy as np
    import time

    # Train model if needed.
    
    if not model._has_persistent_model(TRAINING_DATA):
        d_train = DataLoader()
        d_train.training_data_for_abstracts(TRAINING_DATA)
        model.train(d_train.data,TRAINING_DATA)

    ### Load test query and truth values.  
    d_test = DataLoader()
    query_test, truth = d_test.evaluation_data_for_abstracts(TEST_DATA)
   
   # Apply test query and retrieve results.
    
    minibatches = np.array_split(query_test,int(len(query_test)/BATCHSIZE_EVALUATION))
    
    conferences = list()
    confidences = list()
    
    # Batchify the query to avoid OutOfMemory exceptions.
    
    ###################### MP VERSION POOL #######################

    results = None
    
    def process_ready(r):
        global results
        results = r
    
    pool = mp.Pool(processes=PROCESSES_EVALUATION)
    job = pool.map_async(evaluate_model,minibatches,callback=process_ready)    
    pool.close()
    
    while (True):
        if (job.ready()): break
        print("Tasks remaining: {}".format(job._number_left*job._chunksize))
        time.sleep(5)
        
    print("Tasks completed.")
            
    for result in results:
        conferences.extend(result[0])
        confidences.extend(result[1])
        
    model._load_model(TRAINING_DATA)
     
    ###################### SP VERSION ############################
    """
    model._load_model(TRAINING_DATA)

    for index, minibatch in enumerate(minibatches,1):
        print("Running minibatch [{}/{}]".format(index,len(minibatches)))
        results = model.query_batch(minibatch)
        conferences.extend(results[0])
        confidences.extend(results[1])
    """
    ##############################################################
    
    recommendation = [conferences,confidences]
    
    # Evaluate.
    
    from EvaluationContainer import EvaluationContainer
    evaluation = EvaluationContainer()
    evaluation.evaluate(recommendation,truth)