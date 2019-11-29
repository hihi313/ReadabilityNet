from collections import OrderedDict
import csv, datetime, timeit, os, ntpath, re
from os import listdir
from os.path import isfile, join
from selenium import webdriver
from dis import dis
from lxml import html
from lxml.cssselect import CSSSelector

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
        ######################################################################## add font size
        fontSize_arr = [(9, 0), (10, 0), (11, 0), (12, 0), (13, 0), (14, 0), 
                        (15, 0), (16, 0), (17, 0), (18, 0), (20, 0), (22, 0), 
                        (24, 0), (26, 0), (28, 0), (30, 0), (32, 0), (34, 0), 
                        (36, 0), (40, 0), (44, 0), (48, 0), (56, 0), (64, 0), 
                        (72, 0)]
        self.fontSize = OrderedDict(fontSize_arr)
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

com = CommonVars("./top_100_fonts_lowercase.csv", 
                     "./returnChildNodes.js", 
                     "./returnNodeAttributes.js",
                     "./jquery.js",
                     debug = False)
'''
# using dict is a little bit faster
times = 10000
ffArr = ["arial black", "times new roman", "arial"]
fd = OrderedDict(zip(com.fonts, [0]*len(com.fonts)))
fd2 = fd.fromkeys(fd, 0)
fonts = list(fd.keys())
print(len(com.fonts))
str = datetime.datetime.now()
for i in range(times):
    found = 0
    for a in ffArr:
        f_arr = []  # top N fonts 1/0 array
        for f in fonts:
            if a == f and found == 0:
                found = 1
                f_arr.append(1)
            else:
                f_arr.append(0)
        if found == 1:
            break
    [1 if d == "table-rownone" else 0 for d in com.display_arr]
end = datetime.datetime.now()   
print(end-str)
print(f_arr)
print(len(f_arr))

od = OrderedDict(zip(com.display_arr, [0]*len(com.display_arr)))
od2 = od.fromkeys(od, 0)
str2 = datetime.datetime.now()  
for i in range(times):  
    fd.copy()
    od.copy()
    #tmp = None  
    for a in ffArr:        
        try:
            fd2[a] = 1
            #tmp = a
            break
        except KeyError:
            pass
    od2["table-rownone"]=1
    list(fd.values())+list(od.values())
    
end2 = datetime.datetime.now()  
print(end2-str2)
print(list(fd2.values()))
print(len(fd2))
'''
'''
# range is faster
times = 1000000
str = datetime.datetime.now()
for j in range(times):
    for n in range(9,-1,-1):
        pass
        #print(n, end = '')
end = datetime.datetime.now()  
print("\n", end-str)

str2 = datetime.datetime.now()  
for j in range(times):
    for i in reversed(range(10)):
        pass
        #print(i, end = '')
end2 = datetime.datetime.now()  
print("\n", end2-str2)

print(timeit.timeit('for i in reversed(range(10)):pass', number=times))
print(timeit.timeit('for n in range(9,-1,-1):pass', number=times))
'''

'''
# line continuous & vector dot product test
a = 2
b = 4
c = 8
d = (a
     +b
     -c)
print(d)

arr = [1, 2, 3, 4]
arr2 = [4, 5, 6, 7]
for i in arr:
    print(arr.index(i))

print(sum(i[0] * i[1] for i in zip(arr, arr2)))
'''


def manhattan(x, y):
    if len(x) != len(y):
        raise ValueError("Dict dimension inconsistent:", len(x), len(y), x, y)
    return sum(abs(x[i]-y[i]) for i in range(len(x)))

'''
# start the browser
options = webdriver.ChromeOptions()
options.add_argument("-headless")
options.add_argument("--window-position=0,0")
driver = webdriver.Chrome(options = options)
#set to offline
driver.set_network_conditions(offline=True, latency=0, 
                              throughput=1024 * 1024*1024)
driver.set_window_size(1920, 1080)    
driver.get("file:///" + "D:/Downloads/dragnet_data-master/HTML/test.html") # convert the HTML
     
# start parsing
node = driver.find_element_by_tag_name("html")
rgba = [float(x[0]) for x in re.findall(
            com.num_re, node.value_of_css_property('color'))]
print(node.value_of_css_property('color'))
driver.close()
'''
'''
distances = {k: manhattan([k], [21]) for k, v in com.fontSize.items()}

print(distances)
print(min(distances, key = distances.get))

for k in com.fontSize:
    print(k, com.fontSize[k])
'''
'''
import pandas as pd
import numpy as np
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2

colNames = ["n_char", "n_link", "n_link_char", "n_node", "n_tag", "negAttrPoint", 
            "posAttrPoint", "negTagPoint", "posTagPoint", "CNR", "DS", "LD", 
            "TaD", "TD", "backgroundColor_R", "backgroundColor_G", 
            "backgroundColor_B", "backgroundColor_A", "borderWidth_U", 
            "borderWidth_R", "borderWidth_B", "borderWidth_L", "color_R", 
            "color_O", "color_Y", "color_G", "color_B", "color_P", "color_BL", 
            "color_GR", "color_W", "display_block", "display_contents", 
            "display_flex", "display_grid", "display_inline", 
            "display_inline-block", "display_inline-flex", "display_inline-grid", 
            "display_inline-table", "display_list-item", "display_table", 
            "display_table-caption", "display_table-cell", "display_table-column", 
            "display_table-column-group", "display_table-footer-group", 
            "display_table-header-group", "display_table-row", 
            "display_table-row-group", 
            "gfont_serif", "gfont_sans-serif", "gfont_monospace", "gfont_cursive", "gfont_fantasy", "gfont_system-ui", "gfont_emoji", "gfont_math", "gfont_fangsong", 
            "fontSize_9", "fontSize_10", "fontSize_11", "fontSize_12", "fontSize_13", "fontSize_14", "fontSize_15", "fontSize_16", "fontSize_17", "fontSize_18", "fontSize_20", "fontSize_22", "fontSize_24", "fontSize_26", "fontSize_28", "fontSize_30", "fontSize_32", "fontSize_34", "fontSize_36", "fontSize_40", "fontSize_44", "fontSize_48", "fontSize_56", "fontSize_64", "fontSize_72", 
            "height", "lineHeight", "margin_T", "margin_R", "margin_B", "margin_L", 
            "padding_T", "padding_R", "padding_B", "padding_L", "position_static", "position_absolute", "position_fixed", "position_relative", "position_sticky", "width", "zIndex", "area", "bottom", "right", 
            "show", "x", "y", "yTrain_label"]
print(len(colNames))

data = pd.read_csv("D:\Downloads\webPageData_all.csv", header=None, names=colNames)
X = data.iloc[:,0:107]  #independent columns
print(len(X[0]))
y = data.iloc[:,-1]    #target column i.e price range#apply SelectKBest class to extract top 10 best features
bestfeatures = SelectKBest(score_func=chi2, k=10)
fit = bestfeatures.fit(X,y)
dfscores = pd.DataFrame(fit.scores_)
dfcolumns = pd.DataFrame(X.columns)
#concat two dataframes for better visualization 
featureScores = pd.concat([dfcolumns,dfscores],axis=1)
featureScores.columns = ['Specs','Score']  #naming the dataframe columns
print(featureScores.nlargest(10,'Score'))  #print 10 best features
'''
    
jsons = ["102.json", 
"109.json", 
"116.json", 
"145.json", 
"67.json", 
"134.json", 
"85.json", 
"35.json", 
"142.json", 
"152.json", 
"103.json", 
"94.json", 
"58.json", 
"79.json", 
"88.json", 
"78.json", 
"106.json", 
"128.json", 
"69.json", 
"19.json", 
"20.json", 
"151.json", 
"99.json", 
"119.json", 
"49.json", 
"54.json", 
"14.json", 
"141.json", 
"117.json", 
"42.json", 
"160.json", 
"143.json", 
"97.json", 
"30.json", 
"27.json", 
"60.json", 
"158.json", 
"172.json", 
"28.json", 
"170.json", 
"108.json", 
"39.json", 
"153.json"]
for j in jsons:
    try:
        file = open("D:/Downloads/dragnet_data-master/JSON/" + j, "rb").read()#errors="ignore").read()
        string = file.decode("utf-8")
    except BaseException as err:
        print("file:", j, "ERROR:", err)
print("done")


