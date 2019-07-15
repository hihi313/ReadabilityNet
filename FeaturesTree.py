from anytree import NodeMixin
import threading
from anytree import RenderTree
from math import log, exp

class FeaturesTag(NodeMixin):#non-text node
    def __init__(self, name, parent=None, children=None):
        super(FeaturesTag, self).__init__()
        self.name = name
        self.parent = parent
        if children:
            self.children = children
        #label
        self.label = -1
        #features
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_raw_features = dict(n_char = -1, n_node = -1, n_tag = -1, n_link = -1, n_link_char = -1)
        #Char-Node ratio, Text Density, Tag Density, Link Density, Composite Text Density, Density Sum
        #-1 means not set, cause all these value >= 0
        self.DOM_features = dict(CNR = -1, TD = -1, TaD = -1, LD = -1, CTD = -1, DS = -1)
        
class FeaturesText(NodeMixin):#for text node
    def __init__(self, strValue=-1, parent=None, children=None):
        super(FeaturesText, self).__init__()
        self.name = "String"
        self.strValue = strValue
        self.parent = parent
        if children:
            self.children = children
        #label
        self.label = -1
        #features
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_raw_features = dict(n_char = len(strValue), n_node = 1, n_tag = 0, n_link = 0, n_link_char = 0)
        #cause Text nodes are leaves node and non-tag element, 
        #Text nodes have no Text Density (TD), CTD, LD, DS, n_tag, n_link, n_link_char
        #Char-Node ratio, Text Density, Link Density, Composite Text Density, Density Sum
        #-1 means not set, cause all these value >= 0        
        self.DOM_features = dict(CNR = len(strValue), TaD = 0)
        
class FeaturesTree():#DOM tree features sets
    def __init__(self, html, driver):
        self.html = html
        self.driver = driver
        self.root = None
    def DFT_driver(self):#traverse DOM tree bottom-up, depth first traverse
        self.root = self.DFT(self.html, None)#html is root
        return self.root    
    def DFT(self, node, fParent):
        #create current node
        if type(node) is str:#text node, initial is html element, it's not str object
            fNode = FeaturesText(strValue=node, parent=fParent)
            return
        else:
            fNode = FeaturesTag(name=node.tag_name, parent=fParent)
        #create/compute children features
        for nChild in self.driver.execute_script(open("./returnChildNodes.js").read(), node):#extract every child by JavaScript (invluce text node)
            fChild_thread = threading.Thread(target=self.DFT, args=(nChild, fNode,))#compute the children of f_child features
            fChild_thread.start()
            fChild_thread.join()
        #children features collected
        self.computeFeatures(fNode)#will only compute features for elelment node
        return fNode
    def computeFeatures(self, fNode):#compute node non-css-features (only for element node)
        #summing the features compute from children's/descendents' features
        n_char = n_node = n_tag = n_link = n_link_char = DS = 0
        for fChild in fNode.children:
            n_char += fChild.DOM_raw_features["n_char"]
            n_node += fChild.DOM_raw_features["n_node"]
            n_tag += fChild.DOM_raw_features["n_tag"]
            n_link += fChild.DOM_raw_features["n_link"]
            n_link_char += fChild.DOM_raw_features["n_link_char"]
            if not("DS" in fChild.DOM_features):#key not exist
                DS += 0
            elif fChild.DOM_features["DS"] == -1:
                raise ValueError("%s\'s child %s\'s DS is -1" % (fNode.name, fChild.name))
            else:
                DS += fChild.DOM_features["TD"]#definition of DensitySum is summantion of TextDensity of children
        #compute current node features
        #DOM raw features
        fNode.DOM_raw_features["n_char"] = n_char
        fNode.DOM_raw_features["n_node"] = n_node + 1#current node are included
        fNode.DOM_raw_features["n_tag"] = n_tag + 1        
        if fNode.name == 'a':
            fNode.DOM_raw_features["n_link"] = n_link + 1
            fNode.DOM_raw_features["n_link_char"] = n_char
        else:
            fNode.DOM_raw_features["n_link"] = n_link
            fNode.DOM_raw_features["n_link_char"] = n_link_char
        #DOM features
        Ti = fNode.DOM_raw_features["n_tag"]
        #LCi = fNode.DOM_raw_features["n_link_char"]
        LTi = fNode.DOM_raw_features["n_link"]
        fNode.DOM_features["CNR"] = n_char/fNode.DOM_raw_features["n_node"]
        fNode.DOM_features["TD"] = n_char/Ti
        fNode.DOM_features["TaD"] = Ti/(n_char + 1)
        fNode.DOM_features["LD"] = LTi/(Ti + 1)
        #temporary not used, cause require LCb & Cb under the body element node
        #nLCi = n_char - LCi## of non-link characters under node i         
        #fNode.DOM_features["CTD"] = (n_char/Ti)*log((n_char*Ti/LCi*LTi),log(n_char*LCi/nLCi+LCb*n_char/Cb+exp(1)))
        fNode.DOM_features["DS"] = DS
    def printTree(self, root):
        for pre, _, node in RenderTree(root):
            treestr = u"%s%s" % (pre, node.name)
            print(treestr.ljust(8), getattr(node, "strValue", ""))