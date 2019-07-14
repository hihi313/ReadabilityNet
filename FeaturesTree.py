from anytree import NodeMixin
import threading
from anytree import RenderTree
class FeaturesTag(NodeMixin):#non-text node
    def __init__(self, name, parent=None, children=None):
        super(FeaturesTag, self).__init__()
        self.name = name
        self.parent = parent
        if children:
            self.children = children
        #features
        #Char-Node ratio, Text Density, Tag Density, Link Density, Composite Text Density, Density Sum
        #-1 means not set, cause all these value >= 0
        self.DOM_features = dict(CNR = -1, TD = -1, TaD = -1, LD = -1, CTD = -1, DS = -1)
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_raw_features = dict(n_char = -1, n_node = -1, n_tag = -1, n_link = -1, n_link_char = -1)
class FeaturesText(NodeMixin):#for text node
    def __init__(self, name="String", strValue=-1, parent=None, children=None):
        super(FeaturesText, self).__init__()
        self.name = name
        self.strValue = strValue
        self.parent = parent
        if children:
            self.children = children
        #features
        #cause Text nodes are leaves node and non-tag element, 
        #Text nodes have no Text Density (TD), CTD, LD, DS, n_tag, n_link, n_link_char
        #Char-Node ratio, Text Density, Link Density, Composite Text Density, Density Sum
        #-1 means not set, cause all these value >= 0        
        self.DOM_features = dict(CNR = -1, TaD = -1)
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_raw_features = dict(n_char = -1, n_node = -1)
class FeaturesTree():#DOM tree features sets
    def __init__(self, html, driver):
        self.html = html
        self.driver = driver
        self.root = FeaturesTag(name=html.tag_name)#the html tag as/is root
    def DFT_driver(self):#traverse DOM tree bottom-up, depth first traverse
        self.DFT(self.html, self.root)#html is root
        return self.root    
    def DFT(self, b_node, f_node):
        n_char = n_node = n_tag = n_link = n_link_char = 0
        for b_child in self.driver.execute_script(open("./returnChildNodes.js").read(), b_node):#extract every child by JavaScript (invluce text node)
            if type(b_child) is str:#text node
                f_child = FeaturesText(name="String", strValue=b_child, parent=f_node)
                self.getTextNodeFeatures(f_child)
            else:#element node
                f_child = FeaturesTag(name=b_child.tag_name, parent=f_node)
                if b_child.tag_name == 'a':
                f_child_thread = threading.Thread(target=self.DFT, args=(b_child, f_child,))#compute the children of f_child features
                f_child_thread.start()
                f_child_thread.join()
            #children features collected, summing the features compute from descendents' features
            #self.DOM_raw_features = dict(n_char = -1, n_node = -1, n_tag = -1, n_link = -1, n_link_char = -1)
            n_char += f_child.DOM_raw_features["n_char"]
             
        #compute the current f_node's features derive from raw features
        self.computeFeatures(f_node)
    def getTextNodeFeatures(self, t_node):#compute text node features
            t_node.DOM_raw_features["n_char"] = len(t_node.strValue)#multiple space has been normalize to a space
            t_node.DOM_raw_features["n_node"] = 1
            t_node.DOM_features["CNR"] = len(t_node.strValue)
            t_node.DOM_features["TaD"] = 0
    def sumFeatures(self, parent, child):
        #self.DOM_raw_features = dict(n_char = -1, n_node = -1, n_tag = -1, n_link = -1, n_link_char = -1)
        parent.DOM_raw_features["n_char"] += child.D
    def computeFeatures(self, f_node):#compute element node features
        #self.DOM_features = dict(CNR = -1, TD = -1, TaD = -1, LD = -1, CTD = -1, DS = -1)
        #raw features++ to cancel the initial value
        pass
    def printTree(self, root):
        for pre, _, node in RenderTree(root):
            treestr = u"%s%s" % (pre, node.name)
            print(treestr.ljust(8), getattr(node, "strValue", ""))