from collections import OrderedDict
import csv, datetime
from _ast import Try

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
        self.Nfonts = 100
        self.fonts = [f for f in font_list[:self.Nfonts]
                      if f not in self.gfonts]
        # display property value array
        self.display_arr = ["inline", "block", "contents", "flex", "grid",
                            "inline-block", "inline-flex", "inline-grid",
                            "inline-table", "list-item", "table",
                            "table-caption", "table-column-group",
                            "table-header-group", "table-footer-group",
                            "table-row-group", "table-cell", "table-column",
                            "table-rownone"]

com = CommonVars("./top_100_fonts_lowercase.csv", 
                         "./returnChildNodes.js", 
                         "./returnNodeAttributes.js")

# using dict is not faster
times = 100000
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
    fd2.values()
    fd2[a] = 0
    od2["table-rownone"]=1
    od2.values()
    od2["table-rownone"] = 0
end2 = datetime.datetime.now()  
print(end2-str2)
print(list(fd2.values()))
print(len(fd2))
