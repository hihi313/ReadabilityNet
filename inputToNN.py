import numpy as np, os, threading, FeaturesTree as ft
from anytree.importer import JsonImporter
from collections import OrderedDict

debug = True
printMutex = threading.Lock()
dataMutex = threading.Lock()

def extract(node, xTrain, yTrain, fName):
    # take only FEATURES_TAG as NN input
    if node.type == ft.Type.FEATURES_TAG:
        features = []
        # DOM features
        features = features + list(node.DOM_features.values())
        # DOM derive features
        features = features + list(node.DOM_derive_features.values())
        # CSS features
        CSSFeatures = node.CSS_features.values()
        for f in CSSFeatures:
            try:
                features = features + f
            except TypeError as err:
                features = features + [f]
                if debug:
                    printMutex.acquire()
                    print("file:%s, f:%s, ERROR:%s" % (fName, f, err))
                    printMutex.release()
        # CSS derive features
        features = features + list(node.CSS_derive_features.values())
        # append to input data arrays
        dataMutex.acquire()
        xTrain.append(features)
        yTrain.append(node.label)#yTrain.append(node.similarity)
        dataMutex.release()
    # traverse downward        
    threads = []
    for child in node.children:
        cThread = threading.Thread(target=extract, args=(child, xTrain, yTrain, 
                                                         fName))
        cThread.start()
        threads.append(cThread)
    for t in threads:
        t.join()
        
labeledPath = "D:/Downloads/labeled_JSON/"

files = []
for f in os.listdir(labeledPath):
    p = os.path.join(labeledPath, f)
    if os.path.isfile(p) and f.endswith(".json"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
#files = ["D:/Downloads/labeled_JSON/R427_labeled.json"]

xTrain = []
yTrain = []

threads = []
for f in files:
    importer = JsonImporter(object_pairs_hook = OrderedDict)
    root = importer.read(open(f, encoding="utf-8"))
    print("processing:", f)
    thread = threading.Thread(target=extract, args=(root, xTrain, yTrain, f,))
    thread.start()
    threads.append(thread)
for t in threads:
    t.join()
    
print("done")    
    
xTrain = np.array(xTrain)
yTrain = np.array(yTrain)

np.save(labeledPath + "xTrain.npy", xTrain)
np.save(labeledPath + "yTrain.npy", yTrain)
