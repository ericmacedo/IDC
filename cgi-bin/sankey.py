#!/users/grad/sherkat/anaconda2/bin/python
# Author: Eric Cabral
import sys
import copy
import cgi, cgitb
import json
import os
from fnmatch import fnmatch
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from __future__ import print_function

cgitb.enable()

form = cgi.FieldStorage()

userDirectory = eval(form.getvalue('userDirectory'))

try:
    sessionId = clusterId = fractionId = documentId = transitionId = 0

    colors = [mcolors.to_hex(i) for i in plt.get_cmap("tab20").colors]

    session_dict = dict()
    cluster_dict = dict()
    fraction_dict = dict()
    transition_dict = dict()
    document_dict = dict()

    fileList = os.listdir(userDirectory)
    fileList.sort();

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

        searching = False
        fractions_copy = copy.deepcopy(doc["fractionIds"])
        i = 0
        while(i < session_n):
            if(doc["sessions"][i]):
                if(searching):
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
                searching = not searching
            i += 1

    response = dict({
        "status":"yes",
        "sessions": session_dict,
        "clusters": cluster_dict,
        "fractions": fraction_dict,
        "documents": list(document_dict.values()),
        "transitions": list(transition_dict.values())
    })

    if len(session_n) > 0 :
        print("Content-type:application/json\r\n\r\n")
        print(json.dumps(response))

    else:
        print("Content-type:application/json\r\n\r\n")
        print(json.dumps({'status':'no'}))

except:
    print("Content-type:application/json\r\n\r\n")
    print(json.dumps({'status':'error'}))
