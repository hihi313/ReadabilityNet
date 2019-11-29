from anytree.importer import JsonImporter
from anytree.exporter import JsonExporter
from anytree import RenderTree
import threading, re, datetime, os
import FeaturesTree as ft
from os import listdir
from os.path import isfile, join
from collections import OrderedDict

class Label():
    POSITIVE = 1
    NEGATIVE = 0
    NEUTRAL = 2

# common used variables
class LabelerVars():
    def __init__(self, debug = False):
        # REGEX
        self.space_re = "\s+"
        self.after_comment_re = "!@#\$%\^&\*\(\)\s+COMMENTS"
        # threshold 
        self.label_th = 0.9
        self.shortText_th = 120
        # debug flag
        self.debug = debug
        
class LCSLabeler():
    def __init__(self, comVars, root, gold_standard, fName):
        self.comVars = comVars 
        self.root = root        
        # normalize white space
        tmp_gld = re.sub(self.comVars.space_re, ' ', gold_standard)
        # remove comment
        self.gold_standard = re.sub(self.comVars.after_comment_re, '', tmp_gld)
        self.lock = threading.Lock()
        self.body = None
        self.textNodes = []
        # max properties values
        self.maxZIndex = 0
        # normalize threads
        self.normThreads = []
        if comVars.debug:
            self.fileName = fName
    
    def label_driver(self):
        self.getTextNodes(self.root)
        self.textNodes =sorted(self.textNodes, key=self.getTextNodeLen, 
                               reverse=True)
        self.labelTextNodes()
        self.DFT(self.body, None)
        self.normalize(self.body)
        # wait until all normalize job finish
        for t in self.normThreads:
            t.join()
    
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
    
    '''
    compare & modify gold standard one by one from longest text node, so no 
    need to use pthread_mutex
    '''
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
            # labeling base on # of pos/neg/neu nodes
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
            except BaseException as err:
                print("ERROR:", fName)
                with open(labeledPath + "log/ERROR.log", "a", encoding = 'utf8') as f:
                    f.write(u"json:%s,\tError:%s,\t@DFT\n" % (fName, err))
                    f.close()           
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
            # find the max properties values for normalize stage
            #self.maxZIndex = max(self.maxZIndex, node.CSS_features["zIndex"])
        elif node.type == ft.Type.FEATURES_TEXT:
            try:
                pCollector["n_match"] += node.n_match
                if node.label:
                    pCollector["n_pos"] += 1
                else:
                    pCollector["n_neg"] += 1
            except TypeError:
                pass
        # Tag, just traverse downward
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
        Always normalize space before compare, cause there is modification after 
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
    
    def normalize(self, node):        
        for child in node.children:
            cThread = threading.Thread(target=self.normalize, args=(child,))
            cThread.start()    
            self.normThreads.append(cThread)
        # FEATURES_TAG & FEATURES_TEXT
        if node.type != ft.Type.TAG:
            # normalize DOM raw features
            #normDOMThread = threading.Thread(target=self.normDOM, args=(node,))
            #normDOMThread.start()
            #self.normThreads.append(normDOMThread)
            # only FEATURES_TAG
            if node.type == ft.Type.FEATURES_TAG:
                # normalize CSS features
                normCSSThread = threading.Thread(target=self.normCSS, args=(node,))
                normCSSThread.start()
                normCSSThread.join() # need to norm before add adjust value
                # add adjust value
                #adjThread = threading.Thread(target=self.addAdj, args=(node,))
                #adjThread.start()
                #self.normThreads.append(adjThread)
        
    def normDOM(self, node):
        try:
            node.DOM_features["n_char"] = (node.DOM_features["n_char"]
                                           / self.body.DOM_features["n_char"])
        except ZeroDivisionError:
            pass
        try:
            node.DOM_features["n_node"] = (node.DOM_features["n_node"]
                                           / self.body.DOM_features["n_node"])
        except ZeroDivisionError:
            pass
        try:
            node.DOM_features["n_tag"] = (node.DOM_features["n_tag"]
                                          / self.body.DOM_features["n_tag"])
        except ZeroDivisionError:
            pass
        try:
            node.DOM_features["n_link"] = (node.DOM_features["n_link"]
                                           / self.body.DOM_features["n_link"])
        except ZeroDivisionError:
            pass
        try:
            node.DOM_features["n_link_char"] = (node.DOM_features["n_link_char"]
                                                / self.body.DOM_features["n_link_char"])
        except ZeroDivisionError:
            pass
        try:
            node.DOM_features["n_link_char"] = (node.DOM_features["n_link_char"]
                                                / self.body.DOM_features["n_link_char"])
        except ZeroDivisionError:
            pass
        
    def normCSS(self, node):
        '''
        # color
        try:
            totCharColor = sum(node.CSS_features["color"])
        except BaseException as err:
            if self.comVars.debug:
                print("@normCSS, src:%s, parent:%s, node:%s" % (
                    self.fileName, node.parent.tagName,  
                    getattr(node, "tagName", "TEXT_NODE"), err))
        try:
            node.CSS_features["color"] = [i/totCharColor 
                                          for i in node.CSS_features["color"]]
        except ZeroDivisionError:
            pass
        # fontSize
        totCharFontSize = sum(node.CSS_features["fontSize"])
        try:
            node.CSS_features["fontSize"] = [i/totCharFontSize 
                                          for i in node.CSS_features["fontSize"]]
        except ZeroDivisionError:
            pass
        # line height
        node.CSS_features["lineHeight"] = (node.CSS_features["lineHeight"]
                                           / self.body.CSS_features["lineHeight"])
        
        # border top/right/bottom/left width
        width = node.CSS_features["width"]
        try:
            node.CSS_features["borderWidth"] = [i/width 
                                                for i in node.CSS_features["borderWidth"]]
        except ZeroDivisionError:
            pass
        '''
        try:
            docHeight = self.root.dimension[0]
            docWidth = self.root.dimension[1]
            # margin width
            margin = node.CSS_features["margin"]
            node.CSS_features["margin"] = [margin[0]/docHeight, margin[1]/docWidth,
                                           margin[2]/docHeight, margin[3]/docWidth]
            # padding width
            padding = node.CSS_features["padding"]
            node.CSS_features["padding"] = [padding[0]/docHeight, padding[1]/docWidth,
                                           padding[2]/docHeight, padding[3]/docWidth]
            # height
            node.CSS_features["height"] = node.CSS_features["height"]/docHeight
            # width
            node.CSS_features["width"] = node.CSS_features["width"]/docWidth
            # area
            node.CSS_derive_features["area"] = (node.CSS_derive_features["area"]
                                                / (docHeight * docWidth))
            # geometric: x, y, right, bottom
            node.CSS_derive_features["x"] = node.CSS_derive_features["x"]/docWidth
            node.CSS_derive_features["y"] = node.CSS_derive_features["y"]/docHeight
            node.CSS_derive_features["right"] = (node.CSS_derive_features["right"]
                                                 / docWidth)
            node.CSS_derive_features["bottom"] = (node.CSS_derive_features["bottom"]
                                                  / docWidth)
        except ZeroDivisionError:
            pass
        except BaseException as err:
            print("ERROR:", fName)
            with open(labeledPath + "log/ERROR.log", "a", encoding = 'utf8') as f:
                f.write(u"json:%s,\tError:%s,\t@normCSS\n" % (fName, err))
                f.close()
        '''
        # background color
        node.CSS_features["backgroundColor"] = [i/255 for i in node.CSS_features[
                                                    "backgroundColor"]]
        # z-index
        try:
            node.CSS_features["zIndex"] = (node.CSS_features["zIndex"]
                                           / self.maxZIndex)
        except ZeroDivisionError:
            pass
        '''
     
    # add adjust value and save at CSS_derive_features   
    def addAdj(self, node):
        # font color popularity
        # dot product of node.color & body.color
        node.CSS_derive_features["colorPopularity"] = sum(i[0] * i[1] for i in zip(
                node.CSS_features["color"], self.body.CSS_features["color"]))
        # font size popularity
        node.CSS_derive_features["fontSizePopularity"] = sum(i[0] * i[1] for i in zip(
                node.CSS_features["fontSize"], self.body.CSS_features["fontSize"]))

# debug flag
debug = True
correctPath = "D:/Downloads/baroni2008cleaneval_dataset/cleanEval_goldStandard/"
jsonPath = "D:/Downloads/baroni2008cleaneval_dataset/cleanEval_JSON/"
labeledPath = "D:/Downloads/baroni2008cleaneval_dataset/cleanEval_labeled_JSON_norm/"
fileName_suffix = "_labeled_norm"

def labelAPage(comVars, fName):
    try:
        # open files
        importer = JsonImporter(object_pairs_hook = OrderedDict)
        root = importer.read(open(jsonPath + fName + ".json", encoding="utf-8"))
        gold_standard = open(correctPath + fName + ".txt", encoding="utf-8",
                             errors="ignore").read()
        # start labeling
        str_cvrt = datetime.datetime.now()
        lbler = LCSLabeler(comVars, root, gold_standard, fName)
        lbler.label_driver()
        end_cvrt = datetime.datetime.now()        
        # export as JSON file    
        exporter = JsonExporter(indent=2)
        with open(labeledPath + fName + fileName_suffix + ".json", "w") as f:
            f.write(exporter.export(root))
            # print duration time
            print(f.name, "takes:", end_cvrt - str_cvrt)
            f.close()
        # export degugging log
        if comVars.debug:
            with open(labeledPath + "log/" + fName + fileName_suffix + ".log", "w", 
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
    except BaseException as err:
        print("ERROR:", fName)
        with open(labeledPath + "log/ERROR.log", "a", encoding = 'utf8') as f:
            f.write(u"json:%s,\tError:%s\n" % (fName, err))
            f.close()
            
files = []
for f in listdir(jsonPath):
    p = join(jsonPath, f)
    if isfile(p) and f.endswith(".json"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
# initialize & get common used variables
com = LabelerVars(debug=debug)

#jsons = []
#files = [jsonPath + j for j in jsons]

threads = [] # child threads
shift = 5
start = 0
end = start + shift
while(files[start:end]):            
    for f in files[start:end]:
        # check whether the file has been processed
        fName = re.sub("[\s\S]*[\\/]", '', re.sub("\.[\s\S]*", '', f))
        if not os.path.exists(labeledPath + fName + fileName_suffix + ".json"):
            print("processing:", jsonPath + fName + ".json")
            thread = threading.Thread(target=labelAPage, args=(com, fName))
            thread.start()
            threads.append(thread)
        else:
            print("skip:", f)
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
