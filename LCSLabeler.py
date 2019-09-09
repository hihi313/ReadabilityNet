from anytree.importer import JsonImporter
from anytree.exporter import JsonExporter
from anytree import RenderTree
import threading, re, datetime, os
import FeaturesTree as ft
from os import listdir
from os.path import isfile, join

class Label():
    POSITIVE = 1
    NEGATIVE = 0
    NEUTRAL = 2

# common used variables
class LabelerVars():
    def __init__(self, debug = False):
        # REGEX
        self.space_re = "\s+"
        self.after_comment_re = "!@#\$%\^&\*\(\)\s+COMMENTS[\s\S]*"
        # threshold 
        self.label_th = 0.9
        self.shortText_th = 120
        # debug flag
        self.debug = debug
        
class LCSLabeler():
    def __init__(self, comVars, root, gold_standard):
        self.comVars = comVars 
        self.root = root        
        # normalize white space
        tmp_gld = re.sub(self.comVars.space_re, ' ', gold_standard)
        # remove comment
        self.gold_standard = re.sub(self.comVars.after_comment_re, '', tmp_gld)
        self.lock = threading.Lock()
        self.body = None
        self.textNodes = []
    
    def label_driver(self):
        self.getTextNodes(self.root)
        self.textNodes =sorted(self.textNodes, key=self.getTextNodeLen, 
                               reverse=True)
        self.labelTextNodes()
        self.DFT(self.body, None)
    
    def getTextNodes(self, node):
        # text nodes
        if node.type == ft.Type.FEATURES_TEXT:
            self.textNodes.append(node)
        # element nodes
        else:
            # save the body node
            if node.tagName == "body":
                self.body = node
            # skip anything in <head>
            if node.tagName == "head":
                return
            threads = []
            for child in node.children:
                cThread = threading.Thread(target=self.getTextNodes, 
                                           args=(child,))
                cThread.start()
                threads.append(cThread)
            for t in threads:
                t.join()
    
    def getTextNodeLen(self, node):
        return len(node.strValue)
    
    def labelTextNodes(self):
        for tNode in self.textNodes:
            n_match = self.compare(tNode)
            '''
            If n_match > 0 (have some chars match), delete it from gold standard 
            in order to prevent notation error/noise (for short text)
            Delete the content if full match
            '''
            if n_match > 0:
                # preserving a space in order to prevent words "stick" together
                # count = 1, sub the first result
                self.gold_standard = re.sub(re.escape(tNode.strValue), ' ', 
                                            self.gold_standard, count = 1)
            tNode.n_match = n_match
            try:
                tNode.similarity = n_match/tNode.DOM_features["n_char"]                
            except ZeroDivisionError:
                tNode.similarity = 0
            if tNode.similarity >= self.comVars.label_th:
                tNode.label = 1
            else:
                tNode.label = 0
    
    # label remaining featuresTag node
    # do DFT only in visible <body> tag
    def DFT(self, node, pCollector):
        if node.type == ft.Type.FEATURES_TAG:
            collector = {"n_match": 0, "n_pos": 0, "n_neg": 0, "n_neu": 0}
            threads = []
            for child in node.children:
                cThread = threading.Thread(target=self.DFT, 
                                           args=(child, collector,))
                cThread.start()
                threads.append(cThread)
            for t in threads:
                t.join()
            node.n_match = collector["n_match"]
            try:
                node.similarity = node.n_match/node.DOM_features["n_char"]                
            except ZeroDivisionError:
                node.similarity = 0            
            # labeling & collect for parent
            try:
                pCollector["n_match"] += collector["n_match"]
                if not (collector["n_neu"] or collector["n_pos"]):
                    node.label = Label.NEGATIVE
                    pCollector["n_neg"] += 1
                elif collector["n_neu"] or collector["n_pos"] and collector["n_neg"]:
                    node.label = Label.NEUTRAL
                    pCollector["n_neu"] += 1                
                else:
                    node.label = Label.POSITIVE
                    pCollector["n_pos"] += 1
            except TypeError:
                # not collector , just labeling
                if not (collector["n_neu"] or collector["n_pos"]):
                    node.label = Label.NEGATIVE
                elif collector["n_neu"] or collector["n_pos"] and collector["n_neg"]:
                    node.label = Label.NEUTRAL
                else:
                    node.label = Label.POSITIVE
        elif node.type == ft.Type.FEATURES_TEXT:
            try:
                pCollector["n_match"] += node.n_match
                if node.label:
                    pCollector["n_pos"] += 1
                else:
                    pCollector["n_neg"] += 1
            except TypeError:
                pass
        else:
            threads = []
            for child in node.children:
                cThread = threading.Thread(target=self.DFT, 
                                           args=(child, None,))
                cThread.start()
                threads.append(cThread)
            for t in threads:
                t.join()

    # compare node's string value only for text node
    def compare(self, node):
        '''
        Always normalize before compare, cause there is modification after 
        comparison
        '''
        # normalize space in text node's text
        txt = re.sub(self.comVars.space_re, ' ', node.strValue)
        # normalize space in gold standard
        self.gold_standard = re.sub(self.comVars.space_re, ' ', 
                                    self.gold_standard)
        # for short string
        if len(txt) <= self.comVars.shortText_th:
            # full match
            if re.search(re.escape(txt), self.gold_standard) != None: #match
                # the length of matched string
                match = len(node.strValue)
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
    lbler.label_driver()
    end_cvrt = datetime.datetime.now()
    # print duration time
    print(jsonFileName, "takes:", end_cvrt - str_cvrt)      
    # export as JSON file    
    exporter = JsonExporter(indent=2)
    with open("./labeled_JSON/" + jsonFileName + "_labeled.json", "w") as f:
        f.write(exporter.export(root))
        f.close()  
    if comVars.debug:
        with open("./labeled_JSON/log/" + jsonFileName + "_labeled.log", "w", 
                  encoding = 'utf8') as f:
            for pre, _, node in RenderTree(root):
                treestr = u"%s%s" % (pre, getattr(node, "tagName", "STRING"))
                try:
                    f.write(u"%s %s %s %s %s %s\n" % (treestr.ljust(8), 
                                                      node.label, 
                                                      node.similarity, 
                                                      node.n_match, 
                                                      node.DOM_features["n_char"], 
                                                      getattr(node, "strValue", '')))
                except AttributeError: 
                    f.write(u"%s %s\n" % (treestr.ljust(8), 
                                          getattr(node, "strValue", '')))
            f.close()
            
# debug flag
debug = True
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
com = LabelerVars(debug=debug)

jsons = ["D:/OneDrive/Code_Backup/eclipse_workspace/selenium_test2/src/JSON/R249.json"]

threads = [] # child threads
shift = 5
start = 0
end = start + shift
while(jsons[start:end]):            
    for j in jsons[start:end]:
        # check whether the file has been processed
        labeledJSON = exportPath + re.sub("[\s\S]*[\\/]", '', 
                                          re.sub("\.[\s\S]*", '', j)) + "_labeled.json"
        #if not os.path.exists(labeledJSON):
        print("processing:", j)
        thread = threading.Thread(target=labelAPage, 
                                  args=(com, j, correctPath))
        thread.start()
        threads.append(thread)
        #else:
        #    print("skip:", j)
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
