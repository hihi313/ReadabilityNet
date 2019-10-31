import numpy as np, os, threading, FeaturesTree as ft
from anytree.importer import JsonImporter
from collections import OrderedDict

class CustomError(Exception):
    pass

debug = False
printMutex = threading.Lock()
dataMutex = threading.Lock()
fileIndex = 1

xTrain = []
yTrain = []

def append(features, node, fName = None):
    global fileIndex, xTrain, yTrain
    if len(xTrain) >= 1000:
        # store every 1000 data to file
        print(np.array(xTrain).shape, "File:%s, parent:%s, node:%s" % 
              (fName, node.parent.tagName, node.tagName))
        np.save((labeledPath + "xTrain%d.npy") % (fileIndex), 
                np.array(xTrain))
        np.save((labeledPath + "yTrain%d.npy") % (fileIndex), 
                np.array(yTrain))
        fileIndex = fileIndex + 1
        xTrain = []
        yTrain = []
        print("xTrain", xTrain)
    
    xTrain.append(features)
    yTrain.append(node.label)#yTrain.append(node.similarity)
    
    if debug:
        with printMutex:
            try:
                print("File:%s, parent:%s, node:%s" % (fName, node.parent.tagName, node.tagName))
                print("len:%d" % (len(xTrain)))
                for i in xTrain:
                    print(len(i))        
                print("shape:", np.array(xTrain).shape)
                print("shapeY:", np.array(yTrain).shape)
            except BaseException:
                pass

def extract(node, fName):
    global dataMutex, printMutex
    # take only FEATURES_TAG as NN input
    if node.type == ft.Type.FEATURES_TAG:
        try:
            features = []
            # DOM features
            features = features + list(node.DOM_features.values())
            # DOM derive features
            features = features + list(node.DOM_derive_features.values())
            # CSS features
            # fontFamily length inconsist cross file, delete it
            del node.CSS_features["fontFamily"]
            CSSFeatures = node.CSS_features.values()
            for f in CSSFeatures:
                try:
                    features = features + f
                except TypeError as err:
                    features = features + [f]
                    if f == None:
                        raise CustomError("None type accure")
                    if debug:
                        with printMutex:
                            print("file:%s, f:%s, ERROR:%s" % (fName, f, err))
            # CSS derive features
            features = features + list(node.CSS_derive_features.values())
            # append to input data arrays
            with dataMutex:
                append(features, node, fName)
        except CustomError as err:
            # ignore None data
            with printMutex:
                print("ERROR:%s, file:%s, parent:%s, node:%s" % 
                      (err, fName, node.parent, node))
    # traverse downward        
    threads = []
    for child in node.children:
        cThread = threading.Thread(target=extract, args=(child, fName))
        cThread.start()
        threads.append(cThread)
    for t in threads:
        t.join()
        
    try:
        if node.tagName == "html":
            with printMutex:
                print("file:%s finished" % (fName))
    except AttributeError:
        pass
        
labeledPath = "D:/Downloads/labeled_JSON/"

files = []
for f in os.listdir(labeledPath):
    p = os.path.join(labeledPath, f)
    if os.path.isfile(p) and f.endswith(".json"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
#files = files[0:4]#["D:/Downloads/labeled_JSON/R427_labeled.json"]


threads = []
for f in files:
    importer = JsonImporter(object_pairs_hook = OrderedDict)
    root = importer.read(open(f, encoding="utf-8"))
    #print("processing:", f)
    thread = threading.Thread(target=extract, args=(root, f,))
    thread.start()
    threads.append(thread)
for t in threads:
    t.join()
    
print("done")    
    
# store the remaining data
xTrain = np.array(xTrain)
yTrain = np.array(yTrain)

np.save(labeledPath + "xTrain.npy", xTrain)
np.save(labeledPath + "yTrain.npy", yTrain)
