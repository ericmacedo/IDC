#!/home/eric/python3/bin/python
import os
import numpy as np
from enum import Enum
from time import time
from sklearn.utils import shuffle
from gensim.models import Word2Vec
from multiprocessing import cpu_count
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from skfuzzy.cluster import cmeans, cmeans_predict
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.metrics import silhouette_score

def fontSize(value):
    if value >= 60:
        return 6
    elif value >= 40:
        return 5
    else:
        return 4

class ClusterMode(Enum):
    FIRSTRUN = 0
    ITERATE = 1
    UPDATE = 2

class MainModel:
    user = ""
    k = None
    w2v = None
    d2v = None
    clusterNames = list()
    termClusters = None
    documentClusters = None
    silhouette = None
    clusterTerms = None
    softDocs = None
    clusterDocs = None
    softTerms = None
    clusterCloud = None
    clusterKeyTerms = None
    vocabulary = None
    documentSimilarity = None

    def __init__(self, user,
        w2v=None, d2v=None,
        k=None, clusterNames=None,
        termClusters=None, documentClusters=None, silhouette=None,
        clusterTerms=None, softDocs=None, clusterDocs=None, softTerms=None,
        clusterCloud=None, clusterKeyTerms=None, vocabulary=None,
        documentSimilarity=None):
        
        self.user = user
        self.w2v = W2V(user)
        self.d2v = D2V(user)
        self.k = k
        self.clusterNames = clusterNames
        self.termClusters = termClusters
        self.documentClusters = documentClusters
        self.silhouette = silhouette
        self.clusterTerms = clusterTerms
        self.softDocs = softDocs
        self.clusterDocs = clusterDocs
        self.softTerms = softTerms
        self.clusterCloud = clusterCloud
        self.clusterKeyTerms = clusterKeyTerms
        self.vocabulary = vocabulary
        self.documentSimilarity = documentSimilarity

    def update_models(self, data, tags):
        self.w2v.update_model(data)
        self.d2v.update_model(data=data, tags=tags)

    def train_models(self, data, tags): 
        self.w2v.train_model(data)
        self.d2v.train_model(data=data, tags=tags)
    
    def save(self):
        return (self.__class__, self.__dict__)

    def load(self, cls, attributes):
        self = cls.__new__(cls)
        self.__dict__.update(attributes)
        return self
    
## Word2Vec (Gensim implementation)
class W2V:
    # Settings
    user = ""
    
    ## W2V
    ''' Window 
    skipgram window size in both directions (radius), so if:
    window = 5, it will have a window of size of 11 
    (5 left, 1 center and 5 right).
        
    The literature shows that 8 is good window size
    '''
    window = 8
    vec_size = 100            # Number of features
    alpha = 0.025             # Initial learning rate
    min_alpha= 0.0007         # Decrement of the learning rate after each iteration
    hs = 1                    # 0 - Negative sampling; 1 - Hierarchical softmax
    sg = 1                    # 0 - CBOW; 1 - Skipgram
    negative = 15              # Noise words
    ns_exponent = 0.75        # The exponent used to shape the negative sampling distribution
    min_count = 5             # Ignores all words with total frequency lower than this.
    
    ''' Epochs
    Is the number os times the algorithm will iterate through the corpus.
    
    We decided to calculate the number of epochs by the square root of n.
    '''
    epochs = 40
    model_path = ""
    time = None
    
    # Data
    k = None
    newData = list()

    # Minibatch KMeans (Incremental)
    mkm = None
    
    # GMM
    gmm = None
    labels = None
    partMatrix = None
    silhouette = None
    term_seeds = None
    word_clusters = None
    time = None
    corpus_size = 0

    def __init__(self, user):
        self.user = user
        self.model_path = "../users/"+user+"/w2v.model"

    def calculateSample(self):
        if self.corpus_size > 500:
            return 1e-5
        return float(
            1 * (1.0/ (10 ** int(self.corpus_size/100)))
        )

    def save(self):
        return (self.__class__, self.__dict__)

    def load(self, cls, attributes):
        self = cls.__new__(cls)
        self.__dict__.update(attributes)
        return self
    
    def train_model(self, data):
        t = time()
        self.corpus_size = len(data)

        model = Word2Vec(
            min_count=self.min_count,
            window=self.window,
            size=self.vec_size,
            alpha=self.alpha,
            min_alpha=self.min_alpha,
            sample=self.calculateSample(),
            hs=self.hs,
            sg=self.sg,
            negative=self.negative,
            ns_exponent=self.ns_exponent,
            workers=cpu_count(),
            iter=self.epochs
        )

        model.build_vocab(data)
        
        model.train(
            shuffle(data),
            total_examples=model.corpus_count, 
            epochs=self.epochs
        )
        self.time = round((time() - t) / 60, 2)
        
        model.save(self.model_path)
        return model

    def update_model(self, data):
        t = time()
        
        self.corpus_size += len(data)
        
        model = None
        if os.path.isfile(self.model_path):
            model = Word2Vec.load(self.model_path)
            model.wv.init_sims()
            model.sample = self.calculateSample()

            oldVocab = set(model.wv.index2word)
            
            model.build_vocab(  # Updates vocabulary
                sentences=data,
                update=True
            )

            # with open("../users/eric2/out.log", "w") as logFile:
            #     logFile.write("{}".format("Built vocab"))

            model.train(
                shuffle(data),
                total_examples=model.corpus_count, 
                epochs=self.epochs,
            )
            self.time = round((time() - t) / 60, 2)

            # with open("../users/eric2/out.log", "w") as logFile:
            #     logFile.write("{}".format(self.time))
            
            newVocab = set(model.wv.index2word)

            newWords = newVocab.difference(oldVocab)

            indexes = [
                index for index, word in enumerate(newVocab)
                if word in newWords
            ]

            self.newData = [
                model.wv.vectors_norm[i]
                for i in indexes
            ]

            model.save(self.model_path)
            return model
        else:
            return self.train_model(data)
      
    def cluster_words(self, k, seed=None, update=False):
        t = time()
        model = None
        if os.path.isfile(self.model_path):
            model = Word2Vec.load(self.model_path)
            model.wv.init_sims()
        else:
            return dict({
                "status": False,
                "message": "Model not yet trained"
            })

        if seed:
            init_mode = np.zeros((int(k), self.vec_size))
            for i, v in enumerate(seed):
                seeds = [term for term in v]

                size = len(seeds)
                for term in model.wv.most_similar(positive=v, topn=(50 - size)): # size always = 50 
                    seeds.append(term[0])

                # indexes = [
                #     index for index, word in enumerate(model.wv.index2word)
                #     if word in seeds
                # ]
                # init_mode[i] = np.mean([
                #     model.wv.vectors_norm[index]
                #     for index in indexes
                # ], axis=0)

                init_mode[i] = np.mean([
                    model.wv.word_vec(term)
                    for term in seeds
                ], axis=0)
        else:
            init_mode = "k-means++"

        
        self.mkm = KMeans(
            n_clusters=k,
            init=init_mode,
            n_init=1,
            n_jobs=-1,
            tol=1e-5
        ).fit(model.wv.vectors_norm)
        self.k = k

        self.labels = self.mkm.labels_

        self.partMatrix, _, _, _, _, _ = cmeans_predict(
            test_data=model.wv.vectors_norm.T,
            cntr_trained=self.mkm.cluster_centers_,
            m=1.05,
            metric="cosine",
            error=1e-5,
            maxiter=200,
            init=None
        )

        # DOCUMENT CLUSTERING
        self.term_seeds = list()
        self.word_clusters = list()
        for index, centroid in enumerate(self.mkm.cluster_centers_):  # Centroids
            terms = list()
            self.word_clusters.append(dict())
            for j in model.wv.similar_by_vector(centroid, topn=50):
                terms.append(j[0])
                self.word_clusters[index][str(j[0])] = j[1]
            self.term_seeds.append(terms)  # get top 50 term as seed paragraphs
            
        self.silhouette = silhouette_score(
            model.wv.vectors_norm,
            self.labels,
            metric='cosine'
        )

        self.time = round((time() - t) / 60, 2)

        vocabulary = model.wv.index2word
        clusterTerms = dict()
        top = list()
        for i in range(k):
            clusterTerms[i] = list()
            top.append(
                model.wv.most_similar(
                    positive=[self.mkm.cluster_centers_[i]], topn=50 # Form a 50 lenght paragraph as seed
                )
            )

        for index, label in enumerate(self.labels):
            clusterTerms[label].append(vocabulary[index])

        return dict({
            "status": True,
            "n": len(vocabulary),
            "clusterTerms": list(clusterTerms.values()),
            "vocabulary": vocabulary,
            "labels": self.labels,
            "top": top,
            "soft_cluster": self.partMatrix.T,
            "silhouette": self.silhouette,
            "term_seeds": self.term_seeds,
            "words": self.word_clusters,
            "time": self.time
        })

    # def update_cluster(self, k=None):
    #     model = None
    #     if os.path.isfile(self.model_path):
    #         model = Word2Vec.load(self.model_path)
    #     else:
    #         return dict({
    #             "status": False,
    #             "message": "Model not yet trained"
    #         })
        
    #     model.init_sims()
    #     '''
    #     If K changes, creates a new Minibatch-KMeans model with the new K
    #     Else, fits the new data in the new model
    #     '''
    #     if(k != None and self.k != k):  ## Have k changed?
    #         self.mkm = MiniBatchKMeans(
    #             n_clusters=k,
    #             max_iter=500,
    #             n_init=1
    #         ).fit(model.wv.vectors_norm)
    #         self.k = k


    #     self.calculateGMM(model, k)

    #     return dict({
    #         "status": True,
    #         "vocabulary": model.wv.index2word,
    #         "labels": self.labels,
    #         "soft_cluster": self.partMatrix,
    #         "silhouette": self.silhouette,
    #         "term_seeds": self.term_seeds,
    #         "words": self.word_clusters,
    #         "time": self.time
    #     })

    def getWordVecs(self):
        if not os.path.exists(self.model_path):
            return None
        model = Word2Vec.load(self.model_path)
        return model.wv.vectors

## Doc2Vec (Gensim implementation)
class D2V:
    # settings
    user = ""

    # Doc2Vec
    dm = 1                    # 0 - Bag of Words; 1 - Distributed memory
    dm_mean = 1               # 0 - Use the sum of the context word vectors; 1 - Use the mean.
    dm_concat = 0             # use concatenation of context vectors rather than sum/average
    dbow_words = 1            # 1 - trains word-vectors(skip-gram) simultaneous with DBOW doc-vector training;
    vector_size = 100         # Dimensionality of the feature vectors.
    window = 8   
    alpha = 0.025             # Initial learning rate
    min_alpha = 0.0007        # Decrement of the learning rate after each iteration
    hs = 0                    # 0 - Negative sampling; 1 - Hierarchical softmax
    negative = 15              # Noise words
    ns_exponent = 0.75        # The exponent used to shape the negative sampling distribution
    min_count = 5             # Ignores all words with total frequency lower than this.
    epochs = 40
    model_path = ""
    time = None
    corpus_size = 0
    
    # Data
    k = None
    
    def __init__(self, user):
        self.user = user
        self.model_path = "../users/"+user+"/d2v.model"

    def save(self):
        return (self.__class__, self.__dict__)

    def load(self, cls, attributes):
        self = cls.__new__(cls)
        self.__dict__.update(attributes)
        return self

    def calculateSample(self):
        if self.corpus_size > 500:
            return 1e-5
        
        return 1 * (1.0/ (10 ** int(self.corpus_size/100)))

    def train_model(self, data, tags):
        t = time()

        self.corpus_size = len(data)

        tagged_data = [
            TaggedDocument(
                d,
                tags=[tags[i]]
            ) for i, d in enumerate(data)
        ]

        model = Doc2Vec(
            dm=self.dm,
            dm_mean=self.dm_mean,
            dbow_words=self.dbow_words,
            dm_concat=self.dm_concat,
            vector_size=self.vector_size,
            window=self.window,
            alpha=self.alpha,
            min_alpha=self.min_alpha,
            hs=self.hs,
            sample=self.calculateSample(),
            negative=self.negative,
            ns_expoent=self.ns_exponent,
            min_count=self.min_count,
            workers=cpu_count(),
            epochs=self.epochs
        )

        model.build_vocab(documents=tagged_data)

        model.train(
            documents=shuffle(tagged_data),
            total_examples=model.corpus_count,
            epochs=model.epochs
        )

        self.time = round((time() - t) / 60, 2)

        model.save(self.model_path)
        return model

    def update_model(self, data, tags):
        t = time()

        self.corpus_size += len(data)

        model = None
        if os.path.isfile(self.model_path):
            model = Doc2Vec.load(self.model_path)

            model.docvecs.init_sims()

            count = len(model.docvecs.vectors_docs)
            tagged_data = list()

            oldCorpus = set(model.docvecs.doctags.keys())

            for i, d in enumerate(data):
                tagged_data.append(
                    TaggedDocument(d, tags=[tags[i]])
                )
                count += 1
            
            #model.build_vocab(  # Updates vocabulary
                #sentences=tagged_data,
                #update=True
            #)

            model.train(
                documents=shuffle(tagged_data),
                total_examples=model.corpus_count,
                epochs=model.epochs
            )

            self.time = round((time() - t) / 60, 2)

            newCorpus = set(model.docvecs.doctags.keys())

            newData = newCorpus.difference(oldCorpus)

            self.newData = [
                model.docvecs.vectors_docs_norm[
                    int(model.docvecs.doctags[str(doc)].offset)
                ] for doc in newData
            ]
            
            model.save(self.model_path)
            return model
        else:
            return self.train_model(data, tags)

    def cluster_documents(self, k, seeds=None):
        t = time()
        model = None
        if os.path.isfile(self.model_path):
            model = Doc2Vec.load(self.model_path)
        else:
            return dict({
                "status": False,
                "message": "Model not yet trained"
            })
        
        model.init_sims()

        doc_seeds = np.array([
            model.infer_vector(np.array(j))
            for j in seeds
        ])
        dist = np.sqrt((doc_seeds ** 2).sum(-1))[...,np.newaxis] # norm l2
        doc_seeds /= dist

        mkm_docs = KMeans(
            n_clusters=k,
            init=doc_seeds,
            n_init=1,
            n_jobs=-1,
            tol=1e-5
        ).fit(model.docvecs.vectors_docs_norm)
        self.labels = mkm_docs.labels_
        
        fcm_partMatrix, _, _, _, _, _ = cmeans_predict(
            test_data=model.docvecs.vectors_docs_norm.T,
            cntr_trained=mkm_docs.cluster_centers_,
            m=1.1,
            metric="cosine",
            error=1e-5,
            maxiter=500,
            init=None
        )

        clusterDocs = dict()
        for i in range(k):
            clusterDocs[str(i)] = list()

        for index, label in enumerate(self.labels):
            clusterDocs[str(label)].append(list(model.docvecs.doctags.keys())[index])


        self.time = round((time() - t) / 60, 2)

        self.silhouette = silhouette_score(
            model.docvecs.vectors_docs_norm,
            self.labels,
            metric='cosine'
        )

        return dict({
            "status": True,
            "n": len(model.docvecs.vectors_docs),
            "labels": self.labels,
            "docClusters": list(clusterDocs.values()),
            "soft_cluster": fcm_partMatrix.T,
            "silhouette": self.silhouette,
            "time": self.time
        })

    def getDocVecs_norm(self):
        if not os.path.exists(self.model_path):
            return None
        model = Doc2Vec.load(self.model_path)
        model.init_sims()
        return model.docvecs.vectors_docs_norm

    def getDocVecs(self):
        if not os.path.exists(self.model_path):
            return None
        model = Doc2Vec.load(self.model_path)
        return model.docvecs.vectors_docs

    def getDocTags(self):
        if not os.path.exists(self.model_path):
            return None
        model = Doc2Vec.load(self.model_path)
        return list(model.docvecs.doctags.keys())
