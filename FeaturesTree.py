from anytree import NodeMixin
import threading
from anytree import RenderTree
#from math import log, exp
import re, csv

class FeaturesTag(NodeMixin):#non-text node
    def __init__(self, name, parent=None, children=None):
        super(FeaturesTag, self).__init__()
        self.name = name
        self.parent = parent
        if children:
            self.children = children
        #label
        self.label = None
        #features
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_features = dict(n_char = None, n_node = None, n_tag = None, n_link = None, n_link_char = None)
        #DOM derive features
        #Char-Node ratio, Text Density, Tag Density, Link Density, Composite Text Density, Density Sum
        #None means not set, cause all these value >= 0
        self.DOM_derive_features = dict(CNR = None, TD = None, TaD = None, LD = None, CTD = None, DS = None)
        #CSS raw feature
        #show = webelement.is_displayed()
        self.CSS_features = dict(color = None, lineHeight = None, fontFamily = None, borderWidth = None,
                                     margin = None, padding = None, width = None, height = None,
                                     display = None)
        #CSS derive features
        self.CSS_derive_features = dict(area = None, coordinate = None, show = None)
class FeaturesText(NodeMixin):#for text node
    def __init__(self, strValue=None, parent=None, children=None):
        super(FeaturesText, self).__init__()
        ############################################primitive may need to be declar as constant############################################################## 
        self.name = "String"
        self.strValue = strValue
        self.parent = parent
        if children:
            self.children = children
        #label
        self.label = None
        #features
        #DOM raw features, no need to compute
        ## of character under(inclusive) the node, # of node(inclusive), # of tag(inclusive), # of link, # of link's character
        self.DOM_features = dict(n_char = len(strValue), n_node = 1, n_tag = 0, n_link = 0, n_link_char = 0)
        #cause Text nodes are leaves node and non-tag element, 
        #Text nodes have no Text Density (TD), CTD, LD, DS, n_tag, n_link, n_link_char
        #Char-Node ratio, Text Density, Link Density, Composite Text Density, Density Sum
        #None means not set, cause all these value >= 0        
        self.DOM_derive_features = dict(CNR = len(strValue), TaD = 0)
                
class FeaturesTree():#DOM tree features sets
    ##################################################prevent using file io, in case wanna pickle the object #############################################
    def __init__(self, html, driver, top_fonts_dir_low, get_children_js_dir):
        self.html = html
        self.driver = driver
        self.root = None
        #common used variables
        #number regex
        self.num_re = "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
        #general fonts
        self.gfonts = ["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
                  "emoji", "math", "fangsong"]
        self.fonts = []# ~= top 100 fonts
        #make top 100 fonts list, fonts name in the file should be lower case
        with open(top_fonts_dir_low, encoding="utf-8") as f:
            reader=csv.reader(f)
            rows=[row[0] for idx, row in enumerate(reader) if idx in range(1, 43)]    
            for i in rows:
                if i in self.gfonts:#not include general font
                    continue
                self.fonts.append(i)
        #length unit regex
        self.length_re = "px"
        #display property value array
        self.display_arr = ["inline", "block", "contents", "flex", "grid", "inline-block", "inline-flex",
                        "inline-grid", "inline-table", "list-item", "table", "table-caption", 
                        "table-column-group", "table-header-group", "table-footer-group", 
                        "table-row-group", "table-cell", "table-column", "table-rownone"]
        #JavaScript file/code to retrieve all children node (include text node) of given node
        self.returnChildeNodes_js = open(get_children_js_dir, "r").read()
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
        for nChild in self.driver.execute_script(self.returnChildeNodes_js, node):#extract every child by JavaScript (invluce text node)
            fChild_thread = threading.Thread(target=self.DFT, args=(nChild, fNode,))#compute the children of f_child features
            fChild_thread.start()
            fChild_thread.join()
        #children features collected
        #compute DOM & CSS features (will only compute features for elelment node)
        dom_thread = threading.Thread(target=self.computeDOMFeatures, 
                                      args=(fNode,))#compute the children of f_child features
        #get CSS features
        css_thread = threading.Thread(target=self.computeCSSFeatures, 
                                      args=(node, fNode,))#compute the children of f_child features
        #start thread
        dom_thread.start()        
        css_thread.start()
        dom_thread.join()
        css_thread.join()
        return fNode
    #compute node non-css-features (only for element node)
    def computeDOMFeatures(self, fNode):
        #summing the features compute from children's/descendents' features
        n_char = n_node = n_tag = n_link = n_link_char = DS = 0
        for fChild in fNode.children:
            n_char += fChild.DOM_features["n_char"]
            n_node += fChild.DOM_features["n_node"]
            n_tag += fChild.DOM_features["n_tag"]
            n_link += fChild.DOM_features["n_link"]
            n_link_char += fChild.DOM_features["n_link_char"]
            if not("DS" in fChild.DOM_derive_features):#key not exist
                DS += 0
            elif fChild.DOM_derive_features["DS"] is None:
                raise ValueError("%s\'s child %s\'s DS is None" % (fNode.name, fChild.name))
            else:
                DS += fChild.DOM_derive_features["TD"]#definition of DensitySum is summantion of TextDensity of children
        #compute current node features
        #DOM raw features
        fNode.DOM_features["n_char"] = n_char
        fNode.DOM_features["n_node"] = n_node + 1#current node are included
        fNode.DOM_features["n_tag"] = n_tag + 1        
        if fNode.name == 'a':
            fNode.DOM_features["n_link"] = n_link + 1
            fNode.DOM_features["n_link_char"] = n_char
        else:
            fNode.DOM_features["n_link"] = n_link
            fNode.DOM_features["n_link_char"] = n_link_char
        #DOM features
        Ti = fNode.DOM_features["n_tag"]
        #LCi = fNode.DOM_features["n_link_char"]
        LTi = fNode.DOM_features["n_link"]
        fNode.DOM_derive_features["CNR"] = n_char/fNode.DOM_features["n_node"]
        fNode.DOM_derive_features["TD"] = n_char/Ti
        fNode.DOM_derive_features["TaD"] = Ti/(n_char + 1)
        fNode.DOM_derive_features["LD"] = LTi/(Ti + 1)
        #temporary not used, cause require LCb & Cb under the body element node
        #nLCi = n_char - LCi## of non-link characters under node i         
        #fNode.DOM_derive_features["CTD"] = (n_char/Ti)*log((n_char*Ti/LCi*LTi),log(n_char*LCi/nLCi+LCb*n_char/Cb+exp(1)))
        fNode.DOM_derive_features["DS"] = DS
    #############################devide into thread########################################################3###############
    #############################combine children/descendant's features#####################################################################
    def computeCSSFeatures(self, node, fNode):
        #color
        color = [float(x[0]) for x in re.findall(self.num_re, node.value_of_css_property('color'))]
        #line-height
        lh_tmp = node.value_of_css_property('line-height')
        if lh_tmp == "normal":
            lineHeight = 1.2
        else:
            lh_tmp = re.findall(self.num_re, lh_tmp)
            lineHeight = float(lh_tmp[0])
        #font-family
        ff_tmp = node.value_of_css_property('font-family').lower()
        ff_arr = re.split("\s*,\s*", re.sub("\"", "", re.sub("\s+", " ", ff_tmp)))#font-family array
        #whether the font present in font-family is in top 100 fonts list
        #if match, ignore the rest(exclude the last(generic font))
        found = 0
        for a in ff_arr:
            f_arr = []#top 100 fonts 1/0 array
            for f in self.fonts:
                if a == f and found == 0:
                    found = 1;
                    f_arr.append(1)                    
                else:
                    f_arr.append(0)
            if found == 1:
                break
        #general fonts 1/0 array, find which generic font in font-family is present
        g_arr = [1 if g==ff_arr[-1] else 0 for g in self.gfonts]
        fontFamily = f_arr + g_arr
        #border-width        
        bw_top = float(re.sub(self.length_re, "", node.value_of_css_property("border-top-width")))
        bw_right = float(re.sub(self.length_re, "", node.value_of_css_property("border-right-width")))
        bw_bottom = float(re.sub(self.length_re, "", node.value_of_css_property("border-bottom-width")))
        bw_left = float(re.sub(self.length_re, "", node.value_of_css_property("border-left-width")))
        borderWidth = [bw_top, bw_right, bw_bottom, bw_left]
        #margin
        mg_top = float(re.sub(self.length_re, "", node.value_of_css_property("margin-top")))
        mg_right = float(re.sub(self.length_re, "", node.value_of_css_property("margin-right")))
        mg_bottom = float(re.sub(self.length_re, "", node.value_of_css_property("margin-bottom")))
        mg_left = float(re.sub(self.length_re, "", node.value_of_css_property("margin-left")))
        margin = [mg_top, mg_right, mg_bottom, mg_left]
        #padding
        pd_top = float(re.sub(self.length_re, "", node.value_of_css_property("padding-top")))
        pd_right = float(re.sub(self.length_re, "", node.value_of_css_property("padding-right")))
        pd_bottom = float(re.sub(self.length_re, "", node.value_of_css_property("padding-bottom")))
        pd_left = float(re.sub(self.length_re, "", node.value_of_css_property("padding-left")))
        padding = [pd_top, pd_right, pd_bottom, pd_left]
        #width, height, area, coordinate (included border & padding)
        rect = node.rect
        width = rect["width"]
        height = rect["height"]
        area = width * height
        coordinate = [rect["x"], rect["y"]]
        #display
        d_tmp = node.value_of_css_property('display')        
        display = [1 if d==d_tmp else 0 for d in self.display_arr]
        #show = webelement.is_displaed()
        show = 1 if node.is_displayed() else 0
        #assign features to fNode
        fNode.CSS_features["color"] = color
        fNode.CSS_features["lineHeight"] = lineHeight
        fNode.CSS_features["fontFamily"] = fontFamily
        fNode.CSS_features["borderWidth"] = borderWidth
        fNode.CSS_features["margin"] = margin
        fNode.CSS_features["padding"] = padding
        fNode.CSS_features["width"] = width
        fNode.CSS_features["height"] = height
        fNode.CSS_features["display"] = display
        fNode.CSS_derive_features["area"] = area
        fNode.CSS_derive_features["coordinate"] = coordinate
        fNode.CSS_derive_features["show"] = show
    def printTree(self, root):
        for pre, _, node in RenderTree(root):
            treestr = u"%s%s" % (pre, node.name)
            print(treestr.ljust(8), getattr(node, "strValue", ""))