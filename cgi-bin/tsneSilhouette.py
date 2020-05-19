#!/home/eric/python/bin/python
# Author: Ehsan Sherkat
from sklearn.metrics import silhouette_score
import cgi, cgitb
import numpy
import scipy
import json
import sys

cgitb.enable()

form = cgi.FieldStorage()

tsneResult = json.loads(form.getvalue('tsneResult'))
tsneLabels = json.loads(form.getvalue('tsneLabels'))

try:
	TsneSilhouette = -10

	#calculate avg silhouette_score
	TsneSilhouette = silhouette_score(numpy.array(tsneResult), numpy.array(tsneLabels), 'cosine')

	if TsneSilhouette > -10 :
		print "Content-type:application/json\r\n\r\n"
		print json.dumps({'status':'yes', 'TsneSilhouette':json.dumps(TsneSilhouette)})
	else:
		print "Content-type:application/json\r\n\r\n"
		print json.dumps({'status':'no'})
except:
	print "Content-type:application/json\r\n\r\n"
	print json.dumps({'status':'error'})
