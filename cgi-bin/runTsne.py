#!/home/vagrant/python3/bin/python
# Author: Ehsan Sherkat
from sklearn.manifold import TSNE
import cgi, cgitb 
import pickle
import json
import sys
import os

try:
	cgitb.enable()

	form = cgi.FieldStorage()

	userDirectory = eval(form.getvalue('userDirectory'))
	userID = eval(form.getvalue('userID'))
	perplexityNew = eval(form.getvalue('perplexityNew'))
	clusteringMethod = eval(form.getvalue("clusteringMethod"))

	# run tsne
	tsnePath = "{0}/tsne".format(userDirectory)

	if not clusteringMethod == "Vi2DC":
		os.system(
			"cat {0}out{1}.Matrix | tr ',' '\t' | ./bhtsne.py -d 2 -p {2} > {3}".format(
				userDirectory, userID, perplexityNew, tsnePath
			)
		)
	else:
		modelPath = "../users/{0}/model.pkl".format(userID)
		if os.path.exists(modelPath):	
			with open(modelPath, "rb") as modelFile:
				model = pickle.load(modelFile)
				tsne = TSNE(
					n_components=2, 
					perplexity=int(perplexityNew),
					learning_rate=500,
					early_exaggeration=1.1,
					init="pca",
					metric="cosine",
					n_iter=500,
					method="barnes_hut"
				)
				
				tsne_embedding = tsne.fit_transform(model.d2v.getDocVecs_norm())

				with open(tsnePath, "w") as tsneFile:
					for line in tsne_embedding:
						tsneFile.write("{0}\t{1}\n".format(line[0], line[1]))

	#sklearn tsne
	# array = np.asarray(utility.read_term_document_matrix(userDirectory + "out" + userID + ".Matrix"))
	# n_components = 2
	# TSNE_model = TSNE(n_components=2, perplexity=30.0, method='barnes_hut')
	# TSNE_result = TSNE_model.fit_transform(array)
	# TSNE_string = ""
	# for i in range(0, len(TSNE_result)):
	#	 for j in range(0, n_components):
	#		 if j == 0:
	#			 TSNE_string += str(repr(TSNE_result[i, j]))
	#		 else:
	#			 TSNE_string += '\t' + str(repr(TSNE_result[i, j]))
	#	 TSNE_string += "\n"
	# TSNE_file = open(tsneFile, 'w')
	# TSNE_file.write(TSNE_string)
	# TSNE_file.close()

	#save perplexity number
	with open("{0}/perplexity".format(userDirectory), 'w') as perplexityFile:
		perplexityFile.write(perplexityNew)

	print("Content-type:application/json\r\n\r\n")
	print(json.dumps({'status':'success'}))
except Exception as e:
	print("Content-type:application/json\r\n\r\n")
	print(json.dumps({'status':'error', 'except':json.dumps(str(e))}))
