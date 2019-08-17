from anytree import NodeMixin, RenderTree
from collections import OrderedDict
import re, threading, csv
#from math import log, exp

# node type
class Type():
    TAG = 0;
    FEATURES_TAG = 1
    FEATURES_TEXT = 2

# common used variables
class CommonVars():
    def __init__(self, fonts_lower_path, returnChildeNode_path, returnNodeAttrs_path):
        # open files
        # get top fonts & convert to array
        with open(fonts_lower_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            font_list = [row["font"] for row in reader] # need to be ordered
        # get required JavaScript script
        self.childNodesJs = open(returnChildeNode_path, "r",
                                  encoding="utf-8").read()
        self.nodeAttributesJs = open(returnNodeAttrs_path, "r",
                                  encoding="utf-8").read()
        # REGEX
        # number
        self.num_re = "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
        # length unit
        self.length_re = "px"
        # colors
        ''' 
        need to be ordered, in oder to convert to array, the dict keys are 
        used to identify the color/give the color a name
        '''
        self.colors = OrderedDict()
        self.colors["red"] = (255, 0, 0, 1)  # red
        self.colors["orange"] = (255, 165, 0, 1) # orange
        self.colors["yellow"] = (255, 255, 0, 1) # yellow
        self.colors["green"] = (0, 255, 0, 1) # green
        self.colors["blue"] = (0, 0, 255, 1) # blue
        self.colors["purple"] = (128, 0, 128, 1) # purple
        self.colors["black"] = (0, 0, 0, 1) # black
        self.colors["gray"] = (128, 128, 128, 1) # gray
        self.colors["white"] = (255, 255, 255, 1) # white
        # general fonts
        self.gfonts = ["serif", "sans-serif", "monospace", "cursive",
                       "fantasy", "system-ui", "emoji", "math", "fangsong"]
        # top N fonts
        self.Nfonts = 42
        ######################################################################## has repeated font name
        self.fonts = [f for f in font_list[:self.Nfonts]
                      if f not in self.gfonts]
        # display property value array
        self.display_arr = ["inline", "block", "contents", "flex", "grid",
                            "inline-block", "inline-flex", "inline-grid",
                            "inline-table", "list-item", "table",
                            "table-caption", "table-column-group",
                            "table-header-group", "table-footer-group",
                            "table-row-group", "table-cell", "table-column",
                            "table-row"]
        # position property array
        self.position_arr = ["static", "absolute", "fixed", "relative", "sticky"]

# element node
class FeaturesTag(NodeMixin):
    def __init__(self, tagName, parent=None, children=None):
        super(FeaturesTag, self).__init__()
        self.type = Type.FEATURES_TAG
        self.tagName = tagName
        self.parent = parent
        if children:
            self.children = children
        # label
        self.label = None
        # features
        # DOM raw features, no need to compute
        ''' 
        # character, # node, # tag, # link, # link's character under the node
        (inclusive)
        '''
        self.DOM_features = {"n_char": None, "n_node": None, "n_tag": None,
                             "n_link": None, "n_link_char": None}
        # DOM derive features
        '''
        # Char-Node ratio, Text Density, Tag Density, Link Density, 
        Composite Text Density, Density Sum, "None" means not set
        '''
        self.DOM_derive_features = {"CNR": None, "TD": None, "TaD": None,
                                    "LD": None, "CTD": None, "DS": None}
        # CSS raw feature
        '''
        show = webelement.is_displayed()
        '''
        self.CSS_features = {"color": None, "lineHeight": None,
                             "fontFamily": None, "borderWidth": None,
                             "margin": None, "padding": None, "width": None,
                             "height": None, "backgroundColor": None,
                             "display": None, "position": None, "zIndex": None}
        # CSS derive features
        '''
        x = left, y = top
        '''
        self.CSS_derive_features = {"area": None, "x": None, "y": None,
                                    "right": None, "bottom": None, "show": None}

# text node
class FeaturesText(NodeMixin):
    def __init__(self, strValue=None, parent=None, children=None):
        super(FeaturesText, self).__init__()
        # primitive may need to be de
        self.type = Type.FEATURES_TEXT
        self.strValue = strValue
        self.parent = parent
        if children:
            self.children = children
        # label
        self.label = None
        # features
        # DOM raw features, no need to compute
        ''' 
        # character, # node, # tag, # link, # link's character under the node
        (inclusive)
        '''
        self.DOM_features = {"n_char": len(strValue), "n_node": 1, "n_tag": 0,
                             "n_link": 0, "n_link_char": 0}
        # DOM derive features
        '''
        Text nodes are leaves node and non-tag element, thus Text nodes have no 
        TD, LD, CTD, "None" means not set   
        '''
        self.DOM_derive_features = {"CNR": len(strValue), "TaD": 0, "LD": 0,
                                    "CTD": None}

# for invisible node (tag not in body)
'''
<html>, <head>, <title>, <base>, <meta>
not include : <script>, <style>, <link>, <noscript>
'''
class Tag(NodeMixin):
    def __init__(self, tagName, parent=None, children=None, attrs=None):
        super(Tag, self).__init__()
        # primitive may need to be de
        self.type = Type.TAG
        self.tagName = tagName
        self.parent = parent
        if children:
            self.children = children
        '''
        this kind of tags have no features, cause always invisible
        '''
        # attributes on the node
        if attrs:
            self.attributes = attrs

# DOM tree features Tree constructor
class FeaturesTree():
    def __init__(self, driver, comVars, debug = False):
        self.driver = driver  # used to execute Javascript
        self.url = driver.current_url # used for debug, store the source page
        self.comVars = comVars # common used variables
        self.root = None # root of FeaturesTree
        self.html = None # root of document
        self.head = None # root of some meta data       
        self.debug = debug # used for debug mode to display more informations 

    # traverse DOM tree bottom-up, depth first traverse
    def DFT_driver(self, node):
        self.html = node
        # return root        
        return self.DFT(self.html, None, None, None)

    def DFT(self, node, fParent, pCollector, pInfo):
        collector = None
        # text node
        if type(node) is str:
            # construct text node & compute features
            fNode = FeaturesText(strValue=node, parent=fParent)
        # element node
        else:
            tagName = node.tag_name
            # Tags, have no features, preserve attributes
            if tagName == "html":
                ''' last argument set to True, in order to get the viewport size
                of the current html document which is rendered.
                And store in the html node, as an information
                '''
                result = self.driver.execute_script(self.comVars.nodeAttributesJs,
                                                   node, True,)
                # always root
                fNode = self.root = Tag(tagName = tagName, attrs = result[0], 
                                        parent = None)
                # store the viewport size
                fNode.dimension = result[1]
                # force setting background as white
                self.fork(node, fNode, None, None)
                #no need to compute features & collect features for parent
                return fNode
            elif tagName == "head":
                attrs = self.driver.execute_script(self.comVars.nodeAttributesJs,
                                                   node)
                # always parent at html(root)
                fNode = self.head = Tag(tagName = tagName, attrs = attrs, 
                                        parent = self.root)
                self.fork(node, fNode, None, None)
                #no need to compute features & collect features for parent
                return fNode
            elif tagName == "title" or tagName == "base" or tagName == "meta": 
                attrs = self.driver.execute_script(self.comVars.nodeAttributesJs,
                                                    node)
                # always point these tags' parent at head
                fNode = Tag(tagName = tagName, attrs = attrs, 
                            parent = self.head)
                self.fork(node, fNode, None, None)
                #no need to compute features & collect features for parent
                return fNode
            # FeaturesTags, have features
            else:
                fNode = FeaturesTag(tagName=tagName, parent=fParent)
                # children features collector
                '''
                some features depend on children's feature
                '''
                collector = {"n_char": 0, "n_node": 0, "n_tag": 0, "n_link": 0,
                             "n_link_char": 0, "DS": 0, 
                             "color": self.comVars.colors.fromkeys(
                                                        self.comVars.colors, 0)}
                # current node informations
                '''
                some children's features need to take parent's features consider.
                can be treat as pre-collect the node's features.
                '''
                info = {"colorName": self.getSelfColorName(node), 
                        "backgroundColor": self.getBackgroundColor(pInfo, node)}
                self.fork(node, fNode, collector, info)
                self.computeFeatures(node, fNode, collector, info)
        # (for text node & nodes in <body>) collect features for parent        
        self.collect(fNode, pCollector, pInfo, collector)
        return fNode

    # traverse child nodes
    def fork(self, node, fNode, collector, info):
        # extract every child by JavaScript (include text node)   
        threads = [] # child threads
        for nChild in self.driver.execute_script(self.comVars.childNodesJs, node):
            # compute the children of f_child features                
            fChild_thread = threading.Thread(target=self.DFT,
                                             args=(nChild, fNode, collector,
                                                   info,))
            fChild_thread.start()
            threads.append(fChild_thread)
        for t in threads:
            t.join()

    def computeFeatures(self, node, fNode, collector, info):
        # compute current element node's features,
        # combine current node's features & children's features
        dom_thread = threading.Thread(target=self.computeDOMFeatures,
                                      args=(node, fNode, collector,))
        css_thread = threading.Thread(target=self.computeCSSFeatures,
                                      args=(node, fNode, collector, info,))
        dom_thread.start()
        css_thread.start()
        dom_thread.join()
        css_thread.join()
    
    # collect features for parent's children features collector
    def collect(self, fNode, pCollector, pInfo, collector):        
        try:  # if not None
            pCollector["n_char"] += fNode.DOM_features["n_char"]
            pCollector["n_node"] += fNode.DOM_features["n_node"]
            pCollector["n_tag"] += fNode.DOM_features["n_tag"]
            pCollector["n_link"] += fNode.DOM_features["n_link"]
            pCollector["n_link_char"] += fNode.DOM_features["n_link_char"]
            # text node doesn't have some properties
            if fNode.type == Type.FEATURES_TEXT:
                pCollector["DS"] += 0
                pCollector["color"][pInfo["colorName"]] += fNode.DOM_features["n_char"]
                # skip background color
            else:# element node
                pCollector["DS"] += fNode.DOM_derive_features["TD"]
                #current node's color feature's (array) "values" == collector["color"] (dict)
                pCollector["color"] = addDict(pCollector["color"], 
                                              collector["color"])
        except TypeError as err:
            if self.debug:
                print("@collect, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
        
    # compute element node DOM features
    def computeDOMFeatures(self, node, fNode, collector):
        '''            
        div that contain no block element
        search/score <tag>, class, id by keyword
        dom level/depth of a node
        # image
        '''
        tmp = {}
        tmp["id"] = node.get_attribute("id")
        tmp["class"] = node.get_attribute("class")
        # DOM features
        Ci = fNode.DOM_features["n_char"] = collector["n_char"]
        # current node are included
        fNode.DOM_features["n_node"] = collector["n_node"] + 1
        Ti = fNode.DOM_features["n_tag"] = collector["n_tag"] + 1
        # current node is anchor
        if fNode.tagName == 'a':
            LTi = fNode.DOM_features["n_link"] = collector["n_link"] + 1
            fNode.DOM_features["n_link_char"] = collector["n_char"]
        else:
            LTi = fNode.DOM_features["n_link"] = collector["n_link"]
            fNode.DOM_features["n_link_char"] = collector["n_link_char"]
        # DOM derive features
        fNode.DOM_derive_features["CNR"] = Ci / fNode.DOM_features["n_node"]
        fNode.DOM_derive_features["TD"] = Ci / Ti
        fNode.DOM_derive_features["TaD"] = Ti / (Ci + 1)
        fNode.DOM_derive_features["LD"] = LTi / (Ti + 1)
        '''
        # temporary not used, cause require LCb & Cb under the body element node
        LCi = fNode.DOM_features["n_link_char"]
        nLCi = n_char - LCi# #non-link characters under node i
        fNode.DOM_derive_features["CTD"] = (n_char/Ti)*log((n_char*Ti/LCi*LTi),log(n_char*LCi/nLCi+LCb*n_char/Cb+exp(1)))
        '''
        fNode.DOM_derive_features["DS"] = collector["DS"]

    def computeCSSFeatures(self, node, fNode, collector, info):
        '''
        , z=index, 
        image size statistic
        '''
        tmp = {}
        # displayed background color
        fNode.CSS_features["backgroundColor"] = info["backgroundColor"]
        tmp["borderTopWidth"] = node.value_of_css_property("border-top-width")
        tmp["borderRightWidth"] = node.value_of_css_property("border-right-width")
        tmp["borderBottomWidth"] = node.value_of_css_property("border-bottom-width")
        tmp["borderLeftWidth"] = node.value_of_css_property("border-left-width")
        # color = collector["color"]
        tmp["display"] = node.value_of_css_property('display')
        tmp["fontFamily"] = node.value_of_css_property("font-family")
        tmp["lineHeight"] = node.value_of_css_property("line-height")
        tmp["marginTop"] = node.value_of_css_property("margin-top")
        tmp["marginRight"] = node.value_of_css_property("margin-right")
        tmp["marginBottom"] = node.value_of_css_property("margin-bottom")
        tmp["marginLeft"] = node.value_of_css_property("margin-left")
        tmp["paddingTop"] = node.value_of_css_property("padding-top")
        tmp["paddingRight"] = node.value_of_css_property("padding-right")
        tmp["paddingBottom"] = node.value_of_css_property("padding-bottom")
        tmp["paddingLeft"] = node.value_of_css_property("padding-left")
        tmp["position"] = node.value_of_css_property("position")
        tmp["rect"] = node.rect
        tmp["show"] = node.is_displayed()
        # zIndex no need to convert
        tmp["zIndex"] = node.value_of_css_property("z-index")
                
        threads = []
        # (displayed) background color has been done
        funcs = [self.getBorderWidth, self.getDisplay, self.getFontFamily,
                 self.getGeometric, self.getLineHeight, self.getMargin,
                 self.getPadding, self.getPosition, self.getShow]
        for f in funcs:
            t = threading.Thread(target=f, args=(fNode, tmp,))
            t.start()
            threads.append(t)
        # getColor method take "collector" as argument
        tColor = threading.Thread(target=self.getColor, args=(fNode, collector,))
        tColor.start()
        threads.append(tColor)
        # join
        for t in threads:
            t.join()
       
    # just get current node's color
    def getSelfColorName(self, node):
        rgba = [float(x[0]) for x in re.findall(
            self.comVars.num_re, node.value_of_css_property('color'))]
        distances = {k: manhattan(v, rgba) for k, v in self.comVars.colors.items()}
        #return color name
        return min(distances, key=distances.get)
    
    # get current node's actual display background color
    def getBackgroundColor(self, pInfo, node):
        try:
            rgba = [float(x[0]) for x in re.findall(
                    self.comVars.num_re, node.value_of_css_property('background-color'))]
            return alphaBlending(rgba, pInfo["backgroundColor"])
        except TypeError as err:
            if self.debug:
                print("@getSelfDisplayBackgroundColor, src:%s, parent:%s, node:%s, pInfo:%s\nError:%s" % (
                    self.url,
                    getattr(node.parent, "tag_name", "None"), 
                    getattr(node, "tag_name", "TEXT_NODE"), pInfo, err))
            return alphaBlending(rgba, self.comVars.colors["white"])
    
    def getBorderWidth(self, fNode, tmp):
        bw_top = float(re.sub(self.comVars.length_re, "", tmp["borderTopWidth"]))
        bw_right = float(re.sub(self.comVars.length_re, "", tmp["borderRightWidth"]))
        bw_bottom = float(re.sub(self.comVars.length_re, "", tmp["borderBottomWidth"]))
        bw_left = float(re.sub(self.comVars.length_re, "", tmp["borderLeftWidth"]))
        fNode.CSS_features["borderWidth"] = [bw_top, bw_right, bw_bottom, bw_left]
        
    # get the char color statistic dict of current node 
    def getColor(self, fNode, collector): 
        if self.debug:
            #debug mode, show color name
            fNode.CSS_features["color"] = collector["color"]
        else:
            #convert (ordered) dict to array                     
            fNode.CSS_features["color"] = [collector["color"][k] for k in collector["color"]]

    def getDisplay(self, fNode, tmp):    
        fNode.CSS_features["display"] = [1 if d == tmp["display"] else 0 
                                         for d in self.comVars.display_arr]

    def getFontFamily(self, fNode, tmp):
        # font-family array
        '''
        to lower case, normalize white spaces, remove """, split in to array via 
        ","
        '''
        ff_arr = re.split("\s*,\s*", re.sub("\"", "", re.sub("\s+", " ", 
                                                   tmp["fontFamily"].lower())))
        ''' 
        whether the font present in font-family is in top N fonts list
        if match, ignore the rest(exclude the last(generic font))
        '''
        found = 0
        for a in ff_arr:
            f_arr = []  # top N fonts 1/0 array
            for f in self.comVars.fonts:
                if a == f and found == 0:
                    found = 1
                    f_arr.append(1)
                else:
                    f_arr.append(0)
            if found == 1:
                break
        '''
        general fonts 1/0 array, find which generic font in font-family is
        present. The last one in ff_arr is usually generic  font name
        '''
        g_arr = [1 if g == ff_arr[-1] else 0 for g in self.comVars.gfonts]
        fNode.CSS_features["fontFamily"] = f_arr + g_arr

    def getGeometric(self, fNode, tmp):
        fNode.CSS_features["width"] = tmp["rect"]["width"]
        fNode.CSS_features["height"] = tmp["rect"]["height"]
        fNode.CSS_derive_features["area"] = tmp["rect"]["width"] * tmp["rect"]["height"]
        fNode.CSS_derive_features["x"] = tmp["rect"]["x"]
        fNode.CSS_derive_features["y"] = tmp["rect"]["y"]
        # dimension[1] = width
        fNode.CSS_derive_features["right"] = self.root.dimension[1] - tmp["rect"]["x"] - tmp["rect"]["width"]
        # dimension[0] = height
        fNode.CSS_derive_features["bottom"] = self.root.dimension[0] - tmp["rect"]["y"] - tmp["rect"]["height"]

    def getLineHeight(self, fNode, tmp):
        t = tmp["lineHeight"]
        if t == "normal":
            fNode.CSS_features["lineHeight"] = 1.2
        else:
            fNode.CSS_features["lineHeight"] = float(re.findall(self.comVars.num_re, t)[0])

    def getMargin(self, fNode, tmp):
        mg_top = float(re.sub(self.comVars.length_re, "", tmp["marginTop"]))
        mg_right = float(re.sub(self.comVars.length_re, "", tmp["marginRight"]))
        mg_bottom = float(re.sub(self.comVars.length_re, "", tmp["marginBottom"]))
        mg_left = float(re.sub(self.comVars.length_re, "", tmp["marginLeft"]))
        fNode.CSS_features["margin"] = [mg_top, mg_right, mg_bottom, mg_left]

    def getPadding(self, fNode, tmp):
        pd_top = float(re.sub(self.comVars.length_re, "", tmp["paddingTop"]))
        pd_right = float(re.sub(self.comVars.length_re, "", tmp["paddingRight"]))
        pd_bottom = float(re.sub(self.comVars.length_re, "", tmp["paddingBottom"]))
        pd_left = float(re.sub(self.comVars.length_re, "", tmp["paddingLeft"]))
        fNode.CSS_features["padding"] = [pd_top, pd_right, pd_bottom, pd_left]

    def getPosition(self, fNode, tmp):
        fNode.CSS_features["position"] = [1 if a == tmp["position"] else 0
                                          for a in self.comVars.position_arr]

    #show = webelement.is_displaed()
    def getShow(self, fNode, tmp):        
        fNode.CSS_derive_features["show"] = 1 if tmp["show"] else 0
            
    def getZindex(self, fNode, tmp):
        if tmp["zIndex"] == "auto":
            # set the default value of z-index
            fNode.CSS_features["zIndex"] = 0  
        else:
            fNode.CSS_features["zIndex"] = int(tmp["zIndex"])
    
    def printTree(self, root):
        for pre, _, node in RenderTree(root):
            treestr = u"%s%s" % (pre, node.tagName)
            print(treestr.ljust(8), getattr(node, "strValue", ""))
            
#used to compute the difference between 2 colors
def manhattan(x, y):
    return abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) + abs(x[3] - y[3])

#used to get displayed background color
def alphaBlending(src, dst):
    outA = src[3] + dst[3] * (1 - src[3])
    if outA == 0:
        return (0, 0, 0, 0)
    else:
        outR = (src[0]*src[3] + dst[0]*dst[3] * (1 - src[3]))/outA
        outG = (src[1]*src[3] + dst[1]*dst[3] * (1 - src[3]))/outA
        outB = (src[2]*src[3] + dst[2]*dst[3] * (1 - src[3]))/outA
        return (outR, outG, outB, outA)

def addDict(x, y):
    if len(x) != len(y):
        raise ValueError("Dict dimension inconsistent:", len(x), len(y), x, y)
    else:
        return {k1: v1 + v2 for (k1, v1), v2 in zip(x.items(), y.values())}