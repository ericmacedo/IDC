#!/home/eric/python3/bin/python
#Author: Eric Cabral - 2019
from scipy.spatial.distance import pdist, squareform
from WordEmbeddings import (
    D2V, W2V, 
    MainModel, 
    ClusterMode,
    fontSize
)
import numpy as np
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import cosine_distances
from multiprocessing import cpu_count
from time import time
import cgi, cgitb
import utility
import sys, os
import pickle
import json

try:
    cgitb.enable()
    form = cgi.FieldStorage()
    
    user = eval(form.getvalue('userID'))
    userDirectory = form.getvalue('userDirectory')
    k = int(eval(form.getvalue('clusterNumber'))) # number of clusters
    confidenceUser = float(eval(form.getvalue('confidenceUser')))
    cluster_mode = int(eval(form.getvalue("cluster_mode")))
    term_seeds = eval(form.getvalue("serverData"))  ## get term seeds form

    with open("../users/eric2/out.log", "w") as logFile:
        logFile.write("{}".format(term_seeds))

    if len(term_seeds) == 0: ## No seed
        term_seeds = None

    dataPath = "../users/{0}/model.pkl".format(user)

    model = None
    if os.path.exists(dataPath):  ## If the model is created, loads it
        with open(dataPath, "rb") as modelFile:
            model = pickle.load(modelFile)
    else:  ## Creates a new model
        raise Exception

##  Cluster Terms
    word_cluster = None
    if cluster_mode == ClusterMode.FIRSTRUN.value:
        word_cluster = model.w2v.cluster_words(
            k=k, seed=None, update=False
        )
    elif cluster_mode == ClusterMode.ITERATE.value:
        word_cluster = model.w2v.cluster_words(
            k=k, seed=term_seeds, update=False
        )
    elif cluster_mode == ClusterMode.UPDATE.value:
        word_cluster = model.w2v.cluster_words(
            k=k, 
            seed=term_seeds,
            update=True
        )
    else:
        word_cluster = dict({"status": False})

    if not word_cluster["status"]: ## If found any error
        raise Exception("Error in clustering step")
    
    model.termClusters = word_cluster["clusterTerms"]

    model.clusterNames = eval(form.getvalue("serverClusterName"))

    if len(model.clusterNames) == 0:
        model.clusterNames = ["cluster{0}".format(i) for i in range(k)]
    
    ##  Top 5 terms in Term Clusters
    model.clusterTerms =  list()
    for i in range(k):
        model.clusterTerms.append(dict({
            "cluster": model.clusterNames[i],
            "words": [
                dict({"word": j[0]}) for j in word_cluster["top"][i][:5]
            ]
        }))

    ##  Soft clustering on Terms
    #   {
    #       "name": doc0, "cluster0": value, ..., 'clusterN": value
    #   }
    model.softTerms = list()
    for term in range(word_cluster["n"]):
        model.softTerms.append(dict({
            "name": word_cluster["vocabulary"][term]
        }))
        for index, cluster in enumerate(model.clusterNames):
            model.softTerms[term][cluster] = word_cluster["soft_cluster"][term][index] * 100

    model.clusterCloud = list()
    for i, cluster in enumerate(model.clusterNames):
        model.clusterCloud.append(dict({
            "cluster": cluster,
            "cloud": ""
        }))
        for word in word_cluster["top"][i][:20]:
            model.clusterCloud[i]["cloud"] += "{0}|{1}|".format(word[0],fontSize(word[1]))
        else:
            model.clusterCloud[i]["cloud"] = model.clusterCloud[i]["cloud"][:-1]

    model.clusterKeyTerms = list()
    for index, cluster in enumerate(model.clusterNames):
        model.clusterKeyTerms.append(dict({
            "cluster": cluster,
            "words": [
                dict({
                    "word": word[0],
                    "v1": int(word[1] * 100)
                }) for word in word_cluster["top"][index]
            ]
        }))

    model.vocabulary = word_cluster["vocabulary"]
##  END TERM PART

##  Cluster Documents
    doc_cluster = model.d2v.cluster_documents(k, word_cluster["term_seeds"])

    if not doc_cluster["status"]:   ## If found any error
        raise Exception

    #   Document Clusters
    #   [
    #       [...]
    #   ]
    model.documentClusters = doc_cluster["docClusters"]

    model.docNames = model.d2v.getDocTags()

    ##  Soft clusters on documents
    #   [
    #       { "name": "doc0"," cluster0": value,..., "clusterN": value}
    #   ]
    model.softDocs = list()
    for doc in range(doc_cluster["n"]):
        model.softDocs.append(dict({
            "name": model.docNames[doc]
        }))
        for index, cluster in enumerate(model.clusterNames):
            model.softDocs[doc][cluster] = doc_cluster["soft_cluster"][doc][index] * 100

    ##  Clusters of documents
    #   [
    #       {"cluster": name, "docs": [doc1,...,docN]}
    #   ]
    model.clusterDocs = list()
    for i in range(k):
        model.clusterDocs.append(dict({
            "cluster": model.clusterNames[i],
            "docs": [ 
                dict({"ID": doc}) 
                for doc in doc_cluster["docClusters"][i]
            ]
        }))

    model.documentSimilarity = pairwise_distances(
        model.d2v.getDocVecs(),
        metric="l2",
        n_jobs=cpu_count()
    )

    model.silhouette = doc_cluster["silhouette"]
##  END DOCUMENT PART

    with open(dataPath, "wb") as modelFile:
        pickle.dump(model, modelFile)

    #send data to the Visualization modules
    print("Content-type:application/json\r\n\r\n")
    print(json.dumps({
        'status': 'success',
        "docNames": json.dumps(model.docNames),                                 # OK
        "termSimilarity": json.dumps(model.d2v.getDocVecs_norm().tolist()),     # OK    
        'termClusters':json.dumps(model.termClusters),                          # OK
        'documentClusters':json.dumps(model.documentClusters),                  # OK
        'silhouette': float(model.silhouette),                                  # OK
        "clusterTerms": json.dumps(model.clusterTerms),                         # OK
        "softDocs": json.dumps(model.softDocs),                                 # OK
        "clusterDocs": json.dumps(model.clusterDocs),                           # OK
        "softTerms": json.dumps(model.softTerms),                               # OK
        "clusterCloud": json.dumps(model.clusterCloud),                         # OK
        "clusterKeyTerms": json.dumps(model.clusterKeyTerms),                   # OK
        "allWords": json.dumps(model.vocabulary),                               # OK
        "documentSimilarity": json.dumps(model.documentSimilarity.tolist()),    # OK
    }))
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("Content-type:application/json\r\n\r\n")
    print(json.dumps({'status':'error', 'except':json.dumps(str(e) + " Error line:" + str(exc_tb.tb_lineno) + " Error type:" + str(exc_type) + " File name:" + fname)}))
