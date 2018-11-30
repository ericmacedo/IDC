#!/home/eric/python/bin/python
# Author: Eric Cabral

import sys, logging
import copy
import cgi, cgitb
import json
import os
from fnmatch import fnmatch

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

try:
    cgitb.enable()
    form = cgi.FieldStorage()

    userDirectory = eval(form.getvalue('userDirectory'))
    #userDirectory = "../users/eric/"
    fileList = os.listdir(userDirectory)

    sessionId = clusterId = fractionId = documentId = transitionId = 0

    colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']

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
            "number": sessionId,
            "name": name[0],
            "date": name[1]
            }

            cluster_n = len(session_json["clusterWords"])
            fraction_it = 0
            offset = 0
            for i in range(cluster_n):

                cluster_docs = session_json["clusterDocuments"][i]["docs"]

                clusterId += 1

                # CLUSTERS
                cluster_dict["{0}".format(clusterId)] = dict({
                    "id": clusterId,
                    "name": "Cluster {0}\n, Session {1}".format(i, session_json["fileName"]),
                    "words": [w["word"] for w in session_json["clusterWords"][i]["words"]],
                    "docs": [dict({"id": i["ID"]}) for i in cluster_docs],
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
