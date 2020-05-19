#!/home/eric/python/bin/python
#Author: Eric Cabral - 2019
import cgi, cgitb
import sys, os
import pickle
import json

try:
    cgitb.enable()
    form = cgi.FieldStorage()

    userID = str(eval(form.getvalue('userID')))
    userDirectory = eval(form.getvalue('userDirectory'))

    modelPath = "../users/" + userID + "/model.pkl"

    msg = "true"

    if not os.path.exists(modelPath):
        msg = "false"
    else:
        dirFileList = os.listdir(userDirectory)
        dirFileList = [
            file for file in dirFileList if file.endswith(".txt")
        ]

        with open(modelPath, "rb") as modelFile:
            model = pickle.load(modelFile)

        if len(dirFileList) == len(model.d2v.getDocTags()):
            msg = "false"


    #send data to the Visualization modules
    print "Content-type:application/json\r\n\r\n"
    print json.dumps({'status': msg})
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print "Content-type:application/json\r\n\r\n"
    print json.dumps({'status':'error', 'except':json.dumps(str(e) + " Error line:" + str(exc_tb.tb_lineno) + " Error type:" + str(exc_type) + " File name:" + fname)})
