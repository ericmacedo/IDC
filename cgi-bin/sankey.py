#!/home/eric/python/bin/python
# Author: Eric Cabral

import sys, logging
import copy
import cgi, cgitb
import json
import os
from fnmatch import fnmatch
import numpy as np

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

try:
    cgitb.enable()
    form = cgi.FieldStorage()

    userDirectory = eval(form.getvalue('userDirectory'))
    #userDirectory = "../users/eric/"
    fileList = os.listdir(userDirectory)

    sessionId = clusterId = fractionId = documentId = transitionId = 0

    # https://medialab.github.io/iwanthue/
    # Default pre-set
    # 50 colors 
    # soft (k-means)
    colors = [
        "#6e6af5", "#77c932", "#733ec4", "#51d758", "#ae34ba", "#15a11b", "#a63ec4", "#8eda50", 
        "#9d5ee7", "#74a700", "#c366ef", "#01e286", "#c52cb1", "#00ac50", "#d92dad", "#46df9a",
        "#f42a98", "#2c7900", "#f17dff", "#a5ac00", "#0156cf", "#f1c02f", "#597dff", "#ff9c2a",
        "#1391ff", "#eb6d0d", "#0151af", "#fcba4a", "#7432a1", "#a5d56c", "#ff62db", "#007927",
        "#fa278a", "#00cea0", "#f10d72", "#01a66d", "#d50077", "#01b392", "#e30347", "#2edbe0",
        "#db3522", "#00bed4", "#c93504", "#01ace1", "#d35400", "#0166b7", "#ff8c2f", "#5044a6",
        "#ce8c00", "#d88dff", "#9b8d00", "#87288b", "#bccf65", "#b6007d", "#8fd78d", "#951c78",
        "#d0ca66", "#434a9d", "#db7d00", "#0286ce", "#ff5044", "#01b7b1", "#c6002a", "#5adac5",
        "#ff3d72", "#009976", "#ff71c9", "#006224", "#ff83e5", "#566c00", "#ff9afd", "#807c00",
        "#c79bff", "#bb7b00", "#8da3ff", "#b95900", "#6bbcff", "#a53500", "#028ebf", "#ff8741",
        "#345091", "#e9c25b", "#773a82", "#88d7a8", "#a70043", "#7ed6be", "#a60e29", "#007b4a",
        "#ff72b8", "#365c17", "#efafff", "#535b00", "#b3a5ff", "#916800", "#888ec4", "#95300c",
        "#0198ab", "#ff5861", "#417f5e", "#ff5f8a", "#4a5823", "#ff96ce", "#5c540d", "#fcaee1",
        "#864100", "#766293", "#f6bc6a", "#9e165b", "#d3c784", "#71426e", "#ffa261", "#813e49",
        "#e3c286", "#962b3a", "#a7b078", "#ff86aa", "#6e4c14", "#ff9199", "#80421c", "#ffb2a4",
        "#7e4834", "#ff7462", "#977148", "#ff8f83", "#eaba90", "#b6726b", "#ffac7c", "#d48a90"
    ]

    session_dict = dict()
    cluster_dict = dict()
    fraction_dict = dict()
    transition_dict = dict()
    document_dict = dict()

    fileList = os.listdir(userDirectory)
    fileList.sort()


    for file in fileList:
        if file.endswith('.session'):
            sessionFile = open(userDirectory + file, 'r')
            data = sessionFile.read()
            sessionFile.close()
            session_json = json.loads(data)

            sessionId += 1

            name = session_json["fileName"].split(" @ ")
            # SESSIONS
            session_dict["{0}".format(sessionId)] = {
            "id": sessionId,
            "number": len(session_json['documentClusterData']),
            "name": name[0],
            "date": name[1]
            }

            cluster_n = len(session_json["clusterWords"])
            fraction_it = 0
            offset = 0
            
            clusterDocs = dict()
            
            clusterNames = [ _["cluster"] for _ in session_json["clusterWords"] ]
            
            for clusterName in clusterNames:
				clusterDocs[clusterName] = list()
            
            for document in session_json["documentClusterData"]:
				docName = document["name"]
				docPartMatrix = [
					float(document[_]) for _ in clusterNames
				]
				clusterDocs[
					clusterNames[np.argmax(docPartMatrix)]
				].append(dict({"ID": docName}))
            
            for i in range(cluster_n):

                cluster_docs = clusterDocs[clusterNames[i]]

                clusterId += 1

                # CLUSTERS
                cluster_dict["{0}".format(clusterId)] = dict({
                    "id": clusterId,
                    "name": session_json["clusterWords"][i]["cluster"],
                    "words": [w["word"] for w in session_json["clusterWords"][i]["words"]],
                    "docs": [dict({"id": _["ID"]}) for _ in cluster_docs],
                    "color": colors.pop(0)
                })

                cluster_size = len(cluster_docs)
                fractionId += 1

                # FRACTIONS
                fraction_dict["{0}".format(fractionId)] = dict({
                    "id": fractionId,
                    "order": fraction_it,
                    "clusterId": clusterId,
                    "size": cluster_size,
                    "sessionId": sessionId,
                    "offset": offset
                })
                offset += cluster_size
                fraction_it += 1

                # DOCUMENTS

                for j in cluster_docs:
                    if(j["ID"] in document_dict):
                        document_dict[j["ID"]]["sessions"].append(dict({"clusterId": clusterId}))
                        document_dict[j["ID"]]["fractionIds"].append(fractionId)
                    else:
                        documentId += 1
                        document_dict[j["ID"]] = dict({
                            "id": documentId,
                            "name": j["ID"],
                            "fractionIds": list(),
                            "sessions": list()
                        })

                        for c in range(1, len(session_dict) + 1):
                            if(c == sessionId):
                                document_dict[j["ID"]]["sessions"].append(dict({"clusterId": clusterId}))
                                document_dict[j["ID"]]["fractionIds"].append(fractionId)
                            else:
                                document_dict[j["ID"]]["sessions"].append(dict({}))

    session_n = len(session_dict)

    for doc in document_dict.values():
        if(len(doc["fractionIds"]) == 1):
            continue

        fractions_copy = copy.deepcopy(doc["fractionIds"])

        for i in range(session_n - 1):
            if(doc["sessions"][i]):
                transition = "{0} {1}".format(fractions_copy.pop(0), fractions_copy[0])
                fractions = transition.split(" ")

                if(transition in transition_dict):
                    transition_dict[transition]["number"] += 1
                else:
                    transitionId += 1
                    transition_dict[transition] = dict({
                        "id": transitionId,
                        "from": int(fractions[0]),
                        "to": int(fractions[1]),
                        "number": 1,
                        "leftOffset": 0,
                        "rightOffset": 0
                    })

        fractions_offset = dict()
        for i in fraction_dict.keys():
            fractions_offset[i] = dict({"left":0,"right":0})

        for transition in transition_dict.keys():
            fractions = transition.split(" ")

            transition_dict[transition]["leftOffset"] = fractions_offset[fractions[0]]["right"]
            transition_dict[transition]["rightOffset"] = fractions_offset[fractions[1]]["left"]
            fractions_offset[fractions[0]]["right"] += int(transition_dict[transition]["number"])
            fractions_offset[fractions[1]]["left"] += int(transition_dict[transition]["number"])

    response = dict({
        "status":"yes",
        "sessions": session_dict,
        "clusters": cluster_dict,
        "fractions": fraction_dict,
        "documents": list(document_dict.values()),
        "transitions": list(transition_dict.values())
    })

    if session_n > 0 :
        print("Content-type:application/json\r\n\r\n")
        print(json.dumps(response))

    else:
        print("Content-type:application/json\r\n\r\n")
        print(json.dumps({'status':'no'}))
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print "Content-type:application/json\r\n\r\n"
    print json.dumps({'status':'error', 'except':json.dumps(str(e) + " Error line:" + str(exc_tb.tb_lineno) + " Error type:" + str(exc_type) + " File name:" + fname)})
