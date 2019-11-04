import numpy as np, os, threading, FeaturesTree as ft
from anytree.importer import JsonImporter
from collections import OrderedDict

class CustomError(Exception):
    pass

debug = True
printMutex = threading.Lock()
dataMutex = threading.Lock()
nodeFeaturesLen = 107 # number of features in final result (no normalize)

features = []
labels = []
xTrain = []
yTrain = []

def extract(node, fName):
    global dataMutex, printMutex, features, labels, nodeFeaturesLen
    # traverse downward        
    threads = []
    for child in node.children:
        cThread = threading.Thread(target=extract, args=(child, fName))
        cThread.start()
        threads.append(cThread)
    for t in threads:
        t.join()
    # take only FEATURES_TAG as NN input
    if node.type == ft.Type.FEATURES_TAG:
        try:
            nodeFeatures = []
            # DOM features
            nodeFeatures = nodeFeatures + list(node.DOM_features.values())
            # DOM derive features
            nodeFeatures = nodeFeatures + list(node.DOM_derive_features.values())
            # CSS features
            CSSFeatures = node.CSS_features.values()
            for f in CSSFeatures:
                if f == None:
                        raise CustomError("None type occure")
                try:
                    nodeFeatures = nodeFeatures + f
                except TypeError as err:
                    nodeFeatures = nodeFeatures + [f]                    
            # CSS derive features
            nodeFeatures = nodeFeatures + list(node.CSS_derive_features.values())
            # check if there is None
            if None in nodeFeatures:
                raise CustomError("None type in features")
            # check the features length
            if len(nodeFeatures) > nodeFeaturesLen -1:
                raise CustomError("node's feature's dim inconsistent:%d" %
                                  (len(nodeFeatures)))
            # append to input data arrays
            with dataMutex:
                features.append(nodeFeatures)
                labels.append(node.label)
                '''
                if debug:
                    print(features.index(nodeFeatures), 
                          "parent:%s, node:%s %s" % 
                          (node.parent.tagName, node.tagName, node))
                '''
        except CustomError as err:
            # ignore None data
            if debug:
                with printMutex:
                    print("ERROR:%s, file:%s, parent:%s, node:%s" % 
                          (err, fName, node.parent.tagName, node))
        
labeledPath = "D:/Downloads/labeled_JSON/"
npyPath = "D:/Downloads/NPY/"
fileIndex = 1
N = 100000

files = []
for f in os.listdir(labeledPath):
    p = os.path.join(labeledPath, f)
    if os.path.isfile(p) and f.endswith(".json"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
#files = files[19:20]#["D:/Downloads/labeled_JSON/R427_labeled.json"]

threads = []
for f in files:
    importer = JsonImporter(object_pairs_hook = OrderedDict)
    with open(f, encoding="utf-8") as j:
        root = importer.read(j)
    print(files.index(f), "processing:", f)
    extract(root, f)    
    xTrain = xTrain + features
    yTrain = yTrain + labels
    if debug:
        print("features.shape:", np.array(features).shape)
        print("xTrain.shape:", np.array(xTrain).shape)
        print("yTrain.shape:", np.array(yTrain).shape)
        '''
        for i in range(len(features)):
            print("len(feature[%d]):" % (i), len(features[i]))
        for i in range(len(xTrain)):
            print("len(xTrain[%d]):" % (i), len(xTrain[i]))
        try:
            for i in range(len(yTrain)):
                print("len(yTrain[%d]):" % (i), len(yTrain[i]))
        except TypeError:
            pass
        '''
    features = []
    labels = []
    if len(xTrain) > N:
        np.save(npyPath + "xTrain%d.npy" % (fileIndex), np.array(xTrain))
        np.save(npyPath + "yTrain%d.npy" % (fileIndex), np.array(yTrain))
        fileIndex = fileIndex + 1
        xTrain = []
        yTrain = []
    print("finished:", f)
    
print("done")    
    
# store the remaining data
np.save(npyPath + "xTrain%d.npy" % (fileIndex), np.array(xTrain))
np.save(npyPath + "yTrain%d.npy" % (fileIndex), np.array(yTrain))