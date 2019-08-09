from anytree import NodeMixin, RenderTree
from operator import add
from collections import OrderedDict
import re, threading
#from math import log, exp

# element node
class FeaturesTag(NodeMixin):
    def __init__(self, name, parent=None, children=None):
        super(FeaturesTag, self).__init__()
        self.name = name
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
                             "display": None}
        # CSS derive features
        self.CSS_derive_features = {"area": None, "coordinate": None,
                                    "show": None}

# text node
class FeaturesText(NodeMixin):
    def __init__(self, strValue=None, parent=None, children=None):
        super(FeaturesText, self).__init__()
        # primitive may need to be de
        self.name = "String"
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

# DOM tree features Tree constructor
class FeaturesTree():
    # prevent using file io, i
    def __init__(self, font_list_lower, returnChildeNodes_js):
        self.driver = None  # used to execute Javascript to obtain child Nodes
        self.root = None
        self.html = None
        # common used variables
        # number regex
        self.num_re = "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
        # length unit regex
        self.length_re = "px"
        # colors
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
        ######################################################################## transparent fo backgound color
        # general fonts
        self.gfonts = ["serif", "sans-serif", "monospace", "cursive",
                       "fantasy", "system-ui", "emoji", "math", "fangsong"]
        # top N fonts
        Nfonts = 42
        self.fonts = [f for f in font_list_lower[:Nfonts]
                      if f not in self.gfonts]
        # display property value array
        self.display_arr = ["inline", "block", "contents", "flex", "grid",
                            "inline-block", "inline-flex", "inline-grid",
                            "inline-table", "list-item", "table",
                            "table-caption", "table-column-group",
                            "table-header-group", "table-footer-group",
                            "table-row-group", "table-cell", "table-column",
                            "table-rownone"]
        # JavaScript file/code to retrieve all children node (include text node)
        # of given node
        self.returnChildeNodes_js = returnChildeNodes_js

    # traverse DOM tree bottom-up, depth first traverse
    def DFT_driver(self, driver, node):
        self.driver = driver
        self.html = node
        #html is root
        info = {"bgColor": [self.colors["white"], "white"]}
        self.root = self.DFT(self.html, None, None, info)
        return self.root

    def DFT(self, node, fParent, pCollector, pInfo):
        # text node
        if type(node) is str:
            # construct text node & compute features
            fNode = FeaturesText(strValue=node, parent=fParent)
        # element node
        else:
            fNode = FeaturesTag(name=node.tag_name, parent=fParent)
            # collect children features collector
            cCollector = {"n_char": 0, "n_node": 0, "n_tag": 0, "n_link": 0,
                         "n_link_char": 0, "DS": 0, 
                         ####################################################### turn to ordered dict
                         "color": {k: 0 for k in self.colors},
                         "backgroundColor": {k: 0 for k in self.colors}}
            info = {"color": self.getSelfColor(node), 
                    "bgColor": self.getSelfDisplayBackgroundColor(pInfo,
                                                                       node),
                    "rect": node.rect}
            # extract every child by JavaScript (include text node)
            threads = []
            for nChild in self.driver.execute_script(self.returnChildeNodes_js,
                                                     node):
                # compute the children of f_child features                
                fChild_thread = threading.Thread(target=self.DFT,
                                                 args=(nChild, fNode, cCollector,
                                                       info,))
                fChild_thread.start()
                threads.append(fChild_thread)
            for t in threads:
                t.join()
            # compute current element node's features,
            # combine current node's features & children's features
            dom_thread = threading.Thread(target=self.computeDOMFeatures,
                                          args=(fNode, cCollector,))
            css_thread = threading.Thread(target=self.computeCSSFeatures,
                                          args=(node, fNode, info, cCollector,))
            dom_thread.start()
            css_thread.start()
            dom_thread.join()
            css_thread.join()
        # collect features for parent's children features collector
        ########################################################################adding CSS value (|background) & threaded
        if pCollector:  # if not None
            pCollector["n_char"] += fNode.DOM_features["n_char"]
            pCollector["n_node"] += fNode.DOM_features["n_node"]
            pCollector["n_tag"] += fNode.DOM_features["n_tag"]
            pCollector["n_link"] += fNode.DOM_features["n_link"]
            pCollector["n_link_char"] += fNode.DOM_features["n_link_char"]
            # text node doesn't have some properties
            if type(node) is str:
                pCollector["DS"] += 0
                pCollector["color"][pInfo["color"]] += fNode.DOM_features["n_char"]
                # skip background color
            else:# element node
                pCollector["DS"] += fNode.DOM_derive_features["TD"]
                #current node's color feature's (array) "values" == cCollector["color"] (dict)
                pCollector["color"] = addDict(pCollector["color"], 
                                              cCollector["color"])
                pCollector["backgroundColor"] = addDict(pCollector["backgroundColor"], 
                                                        cCollector["backgroundColor"])

        return fNode

    # compute element node DOM features
    def computeDOMFeatures(self, fNode, cCollector):
        # DOM features
        Ci = fNode.DOM_features["n_char"] = cCollector["n_char"]
        # current node are included
        fNode.DOM_features["n_node"] = cCollector["n_node"] + 1
        Ti = fNode.DOM_features["n_tag"] = cCollector["n_tag"] + 1
        # current node is anchor
        if fNode.name == 'a':
            LTi = fNode.DOM_features["n_link"] = cCollector["n_link"] + 1
            fNode.DOM_features["n_link_char"] = cCollector["n_char"]
        else:
            LTi = fNode.DOM_features["n_link"] = cCollector["n_link"]
            fNode.DOM_features["n_link_char"] = cCollector["n_link_char"]
        # DOM derive features
        fNode.DOM_derive_features["CNR"] = Ci / fNode.DOM_features["n_node"]
        fNode.DOM_derive_features["TD"] = Ci / Ti
        fNode.DOM_derive_features["TaD"] = Ti / (Ci + 1)
        fNode.DOM_derive_features["LD"] = LTi / (Ti + 1)
        # temporary not used, cause require LCb & Cb under the body element node
        #LCi = fNode.DOM_features["n_link_char"]
        # nLCi = n_char - LCi## non-link characters under node i
        #fNode.DOM_derive_features["CTD"] = (n_char/Ti)*log((n_char*Ti/LCi*LTi),log(n_char*LCi/nLCi+LCb*n_char/Cb+exp(1)))
        fNode.DOM_derive_features["DS"] = cCollector["DS"]

    ############################################################################ get properties first then make features computation treaded
    ############################################################################ combine children/descendant's features
    def computeCSSFeatures(self, node, fNode, info, cCollector):
        self.getColor(fNode, cCollector, True)
        getFunc = [self.getLineHeight, self.getFontFamily, 
                    self.getBorderWidth, self.getMargin, self.getPadding,
                    self.getGeometric, self.getDisplay, self.getShow]
        self.getBackgroundColor(fNode, info, cCollector, True)
        threads = []
        for f in getFunc:
            t = threading.Thread(target = f, args = (node, fNode, ))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
       
    # just get current node's color
    def getSelfColor(self, node):
        rgba = [float(x[0]) for x in re.findall(
            self.num_re, node.value_of_css_property('color'))]
        distances = {k: manhattan(v, rgba) for k, v in self.colors.items()}
        #return color name
        return min(distances, key=distances.get)
    
    # get current node's actual display background color
    def getSelfDisplayBackgroundColor(self, pInfo, node):
        rgba = [float(x[0]) for x in re.findall(
                self.num_re, node.value_of_css_property('background-color'))]
        print(pInfo) 
        result =  alphaBlending(rgba, pInfo["bgColor"][0])
       
        distances = {k: manhattan(v, result) for k, v in self.colors.items()}
        #return color name
        return [result, min(distances, key=distances.get)]
    
    def getBackgroundColor(self, fNode, info, cCollector, debug = False):
        fNode.CSS_features["backgroundColor"] = cCollector["backgroundColor"]
        # add self background color area
        bgName = info["bgColor"][1]
        fNode.CSS_features["backgroundColor"][bgName] += info["rect"]["width"] * info["rect"]["height"]
        # minus the overlap area
        for k, v in cCollector["backgroundColor"].items():
            if k != bgName:
                fNode.CSS_features["backgroundColor"][bgName] -= v
        if not debug:
            #convert (ordered) dict to array                     
            fNode.CSS_features["backgroundColor"] = [fNode.CSS_features["backgroundColor"][k] for k in fNode.CSS_features["backgroundColor"]]
    
    # get the char color statistic dict of current node 
    def getColor(self, fNode, cCollector, debug = False): 
        if debug:
            #debug mode, show color name
            fNode.CSS_features["color"] = cCollector["color"]
        else:
            #convert (ordered) dict to array                     
            fNode.CSS_features["color"] = [cCollector["color"][k] for k in cCollector["color"]]

    def getLineHeight(self, node, fNode):
        lh_tmp = node.value_of_css_property('line-height')
        if lh_tmp == "normal":
            lineHeight = 1.2
        else:
            lh_tmp = re.findall(self.num_re, lh_tmp)
            lineHeight = float(lh_tmp[0])
        fNode.CSS_features["lineHeight"] = lineHeight

    def getFontFamily(self, node, fNode):
        ff_tmp = node.value_of_css_property('font-family').lower()
        # font-family array
        ff_arr = re.split("\s*,\s*", re.sub("\"", "",
                                            re.sub("\s+", " ", ff_tmp)))
        ''' 
        whether the font present in font-family is in top N fonts list
        if match, ignore the rest(exclude the last(generic font))
        '''
        found = 0
        for a in ff_arr:
            f_arr = []  # top N fonts 1/0 array
            for f in self.fonts:
                if a == f and found == 0:
                    found = 1
                    f_arr.append(1)
                else:
                    f_arr.append(0)
            if found == 1:
                break
        # general fonts 1/0 array, find which generic font in font-family is
        # present
        g_arr = [1 if g == ff_arr[-1] else 0 for g in self.gfonts]
        fNode.CSS_features["fontFamily"] = f_arr + g_arr

    def getBorderWidth(self, node, fNode):
        bw_top = float(re.sub(self.length_re, "",
                                node.value_of_css_property("border-top-width")))
        bw_right = float(re.sub(self.length_re, "", 
                                node.value_of_css_property("border-right-width")))
        bw_bottom = float(re.sub(self.length_re, "", 
                                 node.value_of_css_property("border-bottom-width")))
        bw_left = float(re.sub(self.length_re, "",
                               node.value_of_css_property("border-left-width")))
        fNode.CSS_features["borderWidth"] = [bw_top, bw_right, bw_bottom, bw_left]

    def getMargin(self, node, fNode):
        mg_top = float(re.sub(self.length_re, "",
                              node.value_of_css_property("margin-top")))
        mg_right = float(re.sub(self.length_re, "", 
                                node.value_of_css_property("margin-right")))
        mg_bottom = float(re.sub(self.length_re, "", 
                                 node.value_of_css_property("margin-bottom")))
        mg_left = float(re.sub(self.length_re, "",
                               node.value_of_css_property("margin-left")))
        fNode.CSS_features["margin"] = [mg_top, mg_right, mg_bottom, mg_left]

    def getPadding(self, node, fNode):
        pd_top = float(re.sub(self.length_re, "",
                              node.value_of_css_property("padding-top")))
        pd_right = float(re.sub(self.length_re, "", 
                                node.value_of_css_property("padding-right")))
        pd_bottom = float(re.sub(self.length_re, "", 
                                 node.value_of_css_property("padding-bottom")))
        pd_left = float(re.sub(self.length_re, "",
                               node.value_of_css_property("padding-left")))
        fNode.CSS_features["padding"] = [pd_top, pd_right, pd_bottom, pd_left]

    def getGeometric(self, node, fNode):
        rect = node.rect
        fNode.CSS_features["width"] = rect["width"]
        fNode.CSS_features["height"] = rect["height"]
        fNode.CSS_derive_features["area"] = rect["width"] * rect["height"]
        fNode.CSS_derive_features["coordinate"] = [rect["x"], rect["y"]]
        
    def getDisplay(self, node, fNode):    
        d_tmp = node.value_of_css_property('display')
        fNode.CSS_features["display"] = [1 if d == d_tmp else 0 for d in self.display_arr]
    
    #show = webelement.is_displaed()
    def getShow(self, node, fNode):        
        fNode.CSS_derive_features["show"] = 1 if node.is_displayed() else 0
    
    def printTree(self, root):
        for pre, _, node in RenderTree(root):
            treestr = u"%s%s" % (pre, node.name)
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
        return {k1: v1 + v2 for (k1, v1), (k2, v2) in zip(x.items(), y.items())}