from anytree.importer import JsonImporter
from anytree.exporter import JsonExporter
from anytree import RenderTree
import threading, re, datetime, os
import FeaturesTree as ft
from os import listdir
from os.path import isfile, join

# common used variables
class LabelerVars():
    def __init__(self):
        # REGEX
        self.space_re = "\s+"
        self.after_comment_re = "!@#\$%\^&\*\(\)\s+COMMENTS[\s\S]*"
        # threshold 
        self.label_th = 0.9
        self.shortText_th = 120
        
class LCSLabeler():
    def __init__(self, comVars, root, gold_standard, debug = False):
        self.comVars = comVars 
        self.root = root        
        # normalize white space
        tmp_gld = re.sub(self.comVars.space_re, ' ', gold_standard)
        # remove comment
        self.gold_standard = re.sub(self.comVars.after_comment_re, '', tmp_gld)
        self.lock = threading.Lock()
        self.debug = debug
    def DFT_driver(self):
        self.DFT(self.root, None)
    def DFT(self, node, pCollector):
        # text node
        if node.type == ft.Type.FEATURES_TEXT:
            #self.lock.acquire()
            match = self.compare(node)
            '''
            If it is content, delete it from gold standard in order to prevent 
            notation error/nois (for short text)
            delete the content if full match
            '''
            '''
            may substitute boilerplate first then, cause content cannot be compare 
            '''
            #self.gold_standard = re.sub(re.escape(node.strValue), '', 
            #                            self.gold_standard, count = 1)
            #self.lock.release()
            # collect for parent
            pCollector["n_match"] += match
            # for debug
            if self.debug:
                node.n_match = match
                node.similarity = match/node.DOM_features["n_char"]
        # element node
        else:
            # # matched char
            collector = {"n_match": 0}        
            threads = []
            for child in node.children:
                cThread = threading.Thread(target=self.DFT, 
                                           args=(child, collector,))
                cThread.start()
                threads.append(cThread)
            for t in threads:
                t.join()
            # labeling
            try:
                node.similarity = collector["n_match"]/node.DOM_features["n_char"]
                if node.similarity >= self.comVars.label_th:
                    node.label = 1
                else:
                    node.label = 0
            except AttributeError: # for node.type == Type.TAG
                pass
            except ZeroDivisionError:
                node.similarity = 0
            # collect for parent
            try:
                pCollector["n_match"] += collector["n_match"]
            except TypeError:# if no pCollector
                pass
            # for debug
            if self.debug:
                node.n_match = collector["n_match"]

    # compare node's string value only for text node
    def compare(self, node):
        txt = re.sub(self.comVars.space_re, ' ', node.strValue)
        # for short string
        if len(txt) < self.comVars.shortText_th:
            # full match
            if re.search(re.escape(txt), self.gold_standard) != None: #match
                match = len(node.strValue)#the length of matched string
            else:
                match = 0
        # for long string
        else:
            match = self.LCS(txt)
        return match

    def LCS(self, txt):
        m = len(self.gold_standard)
        n = len(txt)# length change to normalized length
        c = [[None]*(n + 1) for i in range(m + 1)]
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    c[i][j] = 0
                elif self.gold_standard[i - 1] == txt[j - 1]:
                    c[i][j] = c[i - 1][j - 1] + 1
                else:
                    c[i][j] = max(c[i - 1][j], c[i][j - 1])
        return c[m][n]

################################################################################ normalize features

def labelAPage(comVars, json, correctPath):
    jsonFileName = re.sub("[\s\S]*[\\/]", '', re.sub("\.[\s\S]*", '', json))
    # open the file
    importer = JsonImporter()
    root = importer.read(open(json, encoding="utf-8"))
    gold_standard = open(correctPath + jsonFileName + ".html.corrected.txt",
                         "r", encoding = "utf-8").read()
    # start labeling
    str_cvrt = datetime.datetime.now()
    lbler = LCSLabeler(comVars, root, gold_standard)
    lbler.DFT_driver()
    end_cvrt = datetime.datetime.now()
    # print duration time
    print(jsonFileName, "takes:", end_cvrt - str_cvrt)      
    # export as JSON file    
    exporter = JsonExporter(indent=2)
    with open("./labeled_JSON/" + jsonFileName + "_labeled.json", "w") as f:
        f.write(exporter.export(root))
        f.close()  

correctPath = "D:/Downloads/dragnet_data-master/Corrected/"
jsonPath = "D:/OneDrive/Code_Backup/eclipse_workspace/selenium_test2/src/JSON/"
exportPath = "D:/OneDrive/Code_Backup/eclipse_workspace/selenium_test2/src/labeled_JSON/"
jsons = []
for f in listdir(jsonPath):
    p = join(jsonPath, f)
    if isfile(p) and f.endswith(".json"):
        jsons.append(p)
# sort by size
jsons = sorted(jsons, key=os.path.getsize)
# initialize & get common used variables
com = LabelerVars()

threads = [] # child threads
shift = 5
start = 0
end = start + shift
while(jsons[start:end]):            
    for j in jsons[start:end]:
        # check whether the file has been processed
        labeledJSON = exportPath + re.sub("[\s\S]*[\\/]", '', 
                                          re.sub("\.[\s\S]*", '', j)) + "_labeled.json"
        if not os.path.exists(labeledJSON):
            print("processing:", j)
            thread = threading.Thread(target=labelAPage, args=(com, j, 
                                                               correctPath))
            thread.start()
            threads.append(thread)
        else:
            print("skip:", j)
    for t in threads:
        t.join()
    start = end
    end += shift

print("done")

'''
# used for testing
importer = JsonImporter()
root = importer.read(open("./R249.json", encoding="utf-8"))
gold_standard = open("D:\\Downloads\\dragnet_data-master\\Corrected\\R249.html.corrected.txt",
                     "r", encoding = "utf-8").read()
#print(gold_standard)
comVars = LabelerVars()
str = datetime.datetime.now()
lber = LCSLabeler(comVars, root, gold_standard, debug = True)
lber.DFT_driver()
end = datetime.datetime.now()

for pre, _, node in RenderTree(root):
    try:
        treestr = u"%s%s" % (pre, getattr(node, "tagName", "STRING"))
        print(treestr.ljust(8), 
              getattr(node, "similarity", '-'), 
              getattr(node, "n_match", '-'),
              getattr(node, "DOM_features")["n_char"], 
              getattr(node, "strValue", ''))
    except AttributeError:
        print(treestr.ljust(8), 
                getattr(node, "similarity", '-'), 
                getattr(node, "n_match", '-'),
                "-", 
                getattr(node, "strValue", ''))
    except Exception:
        exporter = JsonExporter(indent=2)
        print(exporter.export(node))
'''
'''
exporter = JsonExporter(indent=2)
print(exporter.export(root))
'''
'''
print(end - str)
'''
