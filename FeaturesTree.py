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
    def __init__(self, fonts_lower_path, returnChildeNode_path, 
                 returnNodeAttrs_path, loadJQuery_path, debug):
        # open/load javascript files
        # get top fonts & convert to array
        with open(fonts_lower_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            font_list = [row["font"] for row in reader] # need to be ordered
        # get required JavaScript script
        self.childNodesJs = open(returnChildeNode_path, "r",
                                  encoding="utf-8").read()
        self.nodeAttributesJs = open(returnNodeAttrs_path, "r",
                                  encoding="utf-8").read()
        self.loadJQuery = open(loadJQuery_path, "r", encoding="utf-8").read()
        self.jQGetMarginTopBottomJs = "var n=$(arguments[0]);return (n.outerHeight(true)-n.outerHeight())/2.0"  
        self.jQGetMarginRightLeftJs = "var n=$(arguments[0]);return (n.outerWidth(true)-n.outerWidth())/2.0"  
        self.jQGetPaddingTopBottomJs = "var n=$(arguments[0]);return (n.innerHeight()-n.height())/2.0"  
        self.jQGetPaddingRightLeftJs = "var n=$(arguments[0]);return (n.innerWidth()-n.width())/2.0"  
        # REGEX
        # number
        self.num_re = "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
        # length unit
        self.length_re = "px"
        # colors
        ''' 
        Using dict to speed up the comparison/finding time.
        And using OrderedDict to preserve order (& for compatability below 
        python 3.6).
        In oder to convert to array, the dict keys are used to identify the 
        color/give the color a name.
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
        '''
        In order to shorten the declaration of OrderedDict, so using 
        (key, value) pair list
        '''
        # general fonts
        gfonts_arr = [("serif", 0), ("sans-serif", 0), ("monospace", 0), 
                       ("cursive", 0), ("fantasy", 0), ("system-ui", 0), 
                       ("emoji", 0), ("math", 0), ("fangsong", 0)]
        self.gfonts = OrderedDict(gfonts_arr)        
        # top N fonts
        self.Nfonts = 42
        fonts_arr = [(f, 0) for f in font_list[:self.Nfonts]
                      if f not in self.gfonts]
        self.fonts = OrderedDict(fonts_arr)
        # display property value array
        display_arr = [("block", 0), ("contents", 0), ("flex", 0), 
                        ("grid", 0), ("inline", 0), ("inline-block", 0), 
                        ("inline-flex", 0), ("inline-grid", 0), 
                        ("inline-table", 0), ("list-item", 0), ("table", 0), 
                        ("table-caption", 0), ("table-cell", 0), 
                        ("table-column", 0), ("table-column-group", 0), 
                        ("table-footer-group", 0), ("table-header-group", 0), 
                        ("table-row", 0), ("table-row-group", 0)]
        self.display = OrderedDict(display_arr)
        # position property array
        position_arr = [("static", 0), ("absolute", 0), ("fixed", 0), 
                         ("relative", 0), ("sticky", 0)]
        self.position = OrderedDict(position_arr)
        '''
        The value of (below) dict is not important
        '''
        # positive tag name
        posTag_arr = [("article", 0), ("blockquote", 0), ("body", 0), 
                       ("div", 0), ("main", 0), ("post", 0), ("pre", 0), 
                       ("td", 0)]
        self.posTag = OrderedDict(posTag_arr)
        # positive tag name
        negTag_arr = [("address", 0), ("aside", 0), ("dd", 0), ("dl", 0), 
                       ("dt", 0), ("footer", 0), ("form", 0), ("li", 0), 
                       ("nav", 0), ("ol", 0), ("th", 0), ("ul", 0)]
        self.negTag = OrderedDict(negTag_arr)
        # positive class, id attribute value
        posAttr_arr = [("and", 0), ("article", 0), ("blockquote", 0), 
                       ("blog", 0), ("body", 0), ("column", 0), ("content", 0), 
                       ("div", 0), ("entry", 0), ("hentry", 0), ("main", 0), 
                       ("page", 0), ("post", 0), ("pre", 0), ("shadow", 0), 
                       ("story", 0), ("td", 0), ("text", 0)]
        self.posAttr = OrderedDict(posAttr_arr)    
        # negative class, id attribute value
        negAttr_arr = [("ad-break", 0), ("address", 0), ("agegate", 0), 
                       ("aside", 0), ("com-", 0), ("combx", 0), ("comment", 0), 
                       ("community", 0), ("contact", 0), ("dd", 0), 
                       ("disqus", 0), ("dl", 0), ("dt", 0), ("extra", 0), 
                       ("footer", 0), ("footnote", 0), ("form", 0), ("li", 0), 
                       ("masthead", 0), ("media", 0), ("menu", 0), ("meta", 0), 
                       ("nav", 0), ("ol", 0), ("outbrain", 0), ("pager", 0), 
                       ("pagination", 0), ("popup", 0), ("promo", 0), 
                       ("related", 0), ("remark", 0), ("rss", 0), ("scroll", 0), 
                       ("shopping", 0), ("shoutbox", 0), ("sidebar", 0), 
                       ("sponsor", 0), ("tags", 0), ("th", 0), ("tool", 0), 
                       ("tweet", 0), ("twitter", 0), ("ul", 0), ("widget", 0)]
        self.negAttr = OrderedDict(negAttr_arr)
        self.debug = debug

# element node
class FeaturesTag(NodeMixin):
    def __init__(self, tagName, parent=None, children=None, debug=False, attrs=None):
        super(FeaturesTag, self).__init__()
        self.type = Type.FEATURES_TAG
        self.tagName = tagName
        self.parent = parent
        if children:
            self.children = children
        # features
        # DOM raw features, no need to compute
        ''' 
        # character, # node, # tag, # link, # link's character under the node
        (inclusive)
        in order to shorten the input features & input layer, posTag, negTag, 
        posAttr, negAttr change to "point"( != "score")
        '''
        self.DOM_features = OrderedDict([("n_char", None), ("n_node", None), 
                                         ("n_tag", None), ("n_link", None), 
                                         ("n_link_char", None), 
                                         ("posTagPoint", None), 
                                         ("negTagPoint", None), 
                                         ("posAttrPoint", None), 
                                         ("negAttrPoint", None)])
        # DOM derive features
        '''
        # Char-Node ratio, Text Density, Tag Density, Link Density, 
        Composite Text Density, Density Sum, "None" means not set
        '''
        self.DOM_derive_features = OrderedDict([("CNR", None), ("TD", None), 
                                                ("TaD", None),("LD", None), 
                                                ("DS", None)])
        # CSS raw feature
        '''
        show = webelement.is_displayed()
        Because of speed concern, split font feature into "fontFamily" & 
        "generalFont" 
        '''
        self.CSS_features = OrderedDict([("color", None), ("lineHeight", None), 
                             ("fontFamily", None), ("borderWidth", None), 
                             ("margin", None), ("padding", None), 
                             ("width", None), ("height", None), 
                             ("backgroundColor", None), ("display", None), 
                             ("position", None), ("zIndex", None)])
        # CSS derive features
        '''
        x = left, y = top
        '''
        self.CSS_derive_features = OrderedDict([("area", None), ("x", None), 
                                                ("y", None), ("right", None), 
                                                ("bottom", None), ("show", None)])
        # used for debug
        if debug:
            self.attrs=attrs

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
        # features
        # DOM raw features, no need to compute
        ''' 
        # character, # node, # tag, # link, # link's character under the node
        (inclusive)
        '''
        self.DOM_features = OrderedDict([("n_char", len(strValue)), 
                                         ("n_node", 1), ("n_tag", 0), 
                                         ("n_link", 0), ("n_link_char", 0)])
        # DOM derive features
        '''
        Text nodes are leaves node and non-tag element, thus Text nodes have no 
        TD, LD, CTD, "None" means not set   
        '''
        self.DOM_derive_features = OrderedDict([("CNR", len(strValue)), 
                                                ("TaD", 0), ("LD", 0)])

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
        # attributes of the node
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
        self.jQueryLoaded = False # whether jquery has been loaded

    # traverse DOM tree bottom-up, depth first traverse
    def DFT_driver(self, node):
        self.html = node
        # return root        
        return self.DFT(self.html, None, None, None)

    def DFT(self, node, fParent, pCollector, pInfo):
        collector = None
        attrs = None
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
                if self.comVars.debug:
                    attrs = self.driver.execute_script(
                        self.comVars.nodeAttributesJs, node)
                fNode = FeaturesTag(tagName=tagName, parent=fParent, 
                                    debug=self.comVars.debug, attrs=attrs)
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
                some children's features need to take parent's features as 
                consider. can be treat as pre-collect the node's features.
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
            if self.comVars.debug:
                print("@collect, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
        
    # compute element node DOM features
    def computeDOMFeatures(self, node, fNode, collector):
        '''            
        ######################################################################## To-do features:
        div that contain no block element
        dom level/depth of a node
        # image
        CTD (composite Text Density)
        '''
        tmp = {}
        tmp["id"] = node.get_attribute("id")
        tmp["class"] = node.get_attribute("class")
        tTag = threading.Thread(target=self.getTagPoint, args=(fNode,))
        tAttr = threading.Thread(target=self.getAttrPoint, args=(fNode, tmp,))
        tTag.start()
        tAttr.start()
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
        
        tTag.join()
        tAttr.join()

    def getTagPoint(self, fNode):
        tagName = fNode.tagName
        fNode.DOM_features["posTagPoint"] = 1 if tagName in self.comVars.posTag else 0
        fNode.DOM_features["negTagPoint"] = 1 if tagName in self.comVars.negTag else 0
        
    def getAttrPoint(self, fNode, tmp):
        posPoint = 0
        negPoint = 0
        try:            
            nId = re.sub("\s+[\s\S]*", '', tmp["id"].lower())            
            if nId in self.comVars.posAttr:
                posPoint += 1
            if nId in self.comVars.negAttr:
                negPoint += 1           
        except AttributeError as err: # if no id
            if self.comVars.debug:
                print("@getAttrPoint_id, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
        try:
            nClass = re.split("\s+", tmp["class"].lower())
            for c in nClass:
                if c in self.comVars.posAttr:
                    posPoint += 1
                if c in self.comVars.negAttr:
                    negPoint += 1
        except AttributeError as err: # if no class
            if self.comVars.debug:
                print("@getAttrPoint_class, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
        fNode.DOM_features["posAttrPoint"] = posPoint
        fNode.DOM_features["negAttrPoint"] = negPoint

    def computeCSSFeatures(self, node, fNode, collector, info):
        '''
        ######################################################################## To-do features:
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
                 self.getPadding, self.getPosition, self.getShow, self.getZindex]
        for f in funcs:
            if f == self.getMargin or f == self.getPadding:
                t = threading.Thread(target=f, args=(fNode, tmp, node,))
            else:
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
            if self.comVars.debug:
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
        if self.comVars.debug:
            #debug mode, show color name
            fNode.CSS_features["color"] = collector["color"]
        else:
            #convert (ordered) dict to array                     
            fNode.CSS_features["color"] = [collector["color"][k] for k in collector["color"]]

    def getDisplay(self, fNode, tmp):
        d = self.comVars.display.copy()
        try:
            d[tmp["display"]] = 1
        except KeyError:
            pass
        fNode.CSS_features["display"] = list(d.values())

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
        fDict = self.comVars.fonts.copy()
        for f in ff_arr:        
            try:
                fDict[f] = 1
                break
            except KeyError:
                pass
        '''
        general fonts 1/0 array, find which generic font in font-family is
        present. The last one in ff_arr is usually generic font name
        '''
        gfDict = self.comVars.gfonts.copy()
        try:
            gfDict[ff_arr[-1]] = 1
        except KeyError:
            pass
        fNode.CSS_features["fontFamily"] = list(fDict.values()) + list(gfDict.values()) 

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
            fNode.CSS_features["lineHeight"] = float(re.findall(self.comVars.num_re, t)[0][0])

    def getMargin(self, fNode, tmp, node):
        try:
            mg_top = float(re.sub(self.comVars.length_re, "", tmp["marginTop"]))            
            mg_bottom = float(re.sub(self.comVars.length_re, "", tmp["marginBottom"]))            
        except ValueError as err: # auto
            if self.comVars.debug:
                print("@getMargin, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
            if not self.jQueryLoaded:
                self.loadJQuery()
            mg_top = mg_bottom = float(self.driver.execute_script(
                self.comVars.jQGetMarginTopBottomJs, node))
        try:
            mg_right = float(re.sub(self.comVars.length_re, "", tmp["marginRight"])) 
            mg_left = float(re.sub(self.comVars.length_re, "", tmp["marginLeft"]))            
        except ValueError as err: # auto
            if self.comVars.debug:
                print("@getMargin, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
            if not self.jQueryLoaded:
                self.loadJQuery()
            mg_right = mg_left = float(self.driver.execute_script(
                self.comVars.jQGetMarginRightLeftJs, node))      
        fNode.CSS_features["margin"] = [mg_top, mg_right, mg_bottom, mg_left]

    def getPadding(self, fNode, tmp, node):
        try:
            pd_top = float(re.sub(self.comVars.length_re, "", tmp["paddingTop"]))            
            pd_bottom = float(re.sub(self.comVars.length_re, "", tmp["paddingBottom"]))            
        except ValueError as err: # auto
            if self.comVars.debug:
                print("@getPadding, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
            if not self.jQueryLoaded:
                self.loadJQuery()
            pd_top = pd_bottom = float(self.driver.execute_script(
                self.comVars.jQGetPaddingTopBottomJs, node))
        try:
            pd_right = float(re.sub(self.comVars.length_re, "", tmp["paddingRight"]))
            pd_left = float(re.sub(self.comVars.length_re, "", tmp["paddingLeft"]))
        except ValueError as err: # auto
            if self.comVars.debug:
                print("@getPadding, src:%s, parent:%s, node:%s\nError:%s" % (
                    self.url,
                    getattr(fNode.parent, "tagName", "None"), 
                    getattr(fNode, "tagName", "TEXT_NODE"), err))
            if not self.jQueryLoaded:
                self.loadJQuery()
            pd_right = pd_left = float(self.driver.execute_script(
                self.comVars.jQGetPaddingRightLeftJs, node))
        fNode.CSS_features["padding"] = [pd_top, pd_right, pd_bottom, pd_left]

    def getPosition(self, fNode, tmp):
        p = self.comVars.position.copy()
        try:
            p[tmp["position"]] = 1
        except KeyError:
            pass
        fNode.CSS_features["position"] = list(p.values())

    #show = webelement.is_displaed()
    def getShow(self, fNode, tmp):        
        fNode.CSS_derive_features["show"] = 1 if tmp["show"] else 0
            
    def getZindex(self, fNode, tmp):
        if tmp["zIndex"] == "auto":
            # set the default value of z-index
            fNode.CSS_features["zIndex"] = 0  
        else:
            fNode.CSS_features["zIndex"] = int(tmp["zIndex"])
            
    def loadJQuery(self):
        self.driver.execute_script(self.comVars.loadJQuery)
        self.jQueryLoaded = True
        
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
        od = OrderedDict()
        for (k1, v1), v2 in zip(x.items(), y.values()):
            od[k1] = v1 + v2
        return od