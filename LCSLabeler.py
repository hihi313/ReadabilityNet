from anytree.importer import JsonImporter
from anytree import RenderTree
import threading, re

class LCSLabeler():
    def __init__(self, root, gold_standard):
        self.root = root
        self.rSpace_re = "\s+"
        self.gold_standard = re.sub(self.rSpace_re, " ", gold_standard)#replace redundant/normalize white space
    def DFT_driver(self):
        self.DFT(self.root)
    def DFT(self, node):
        #initialize the # matched char        
        for Cnode in node.children:
        ############################################primitive may need to be declare as constant################################################## 
            if Cnode.name == "String":#for text node
                Cnode_thread = threading.Thread(target = self.compare, args = (Cnode,))
                Cnode_thread.start()
                Cnode_thread.join()
                continue
            else:#for element node
                Cnode_thread = threading.Thread(target = self.DFT, args = (Cnode,))
                Cnode_thread.start()
                Cnode_thread.join()
        node.matches = 0 
    #compare node's string value only for text node
    def compare(self, node):
        txt = re.sub(self.rSpace_re, " ", node.strValue)
        ####################################################primitive need to declar as constant ##########################################
        if len(txt) < 50:#for short string
            #full match
            if re.search(txt, self.gold_standard) != None: #match
                node.matches = len(node.strValue)#the length of matched string
            else:
                node.matches = 0
        else:#for long string
            node.matches = self.LCS(txt)
    def LCS(self, txt):
        m = len(self.gold_standard)
        n = len(txt)
        c = [[None]*(n + 1) for i in range(m + 1)] 
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    c[i][j] = 0
                elif self.gold_standard[i - 1] == txt[j - 1]:
                    c[i][j] = c[i - 1][j - 1] + 1
                else:
                    c[i][j] = max(c[i][j - 1], c[i - 1][j])
        return c[m][n]

importer = JsonImporter()
root = importer.read(open("./featuresTree_test.json", encoding="utf-8"))
gold_standard = open("D:\\Downloads\\dragnet_data-master\\Corrected\\83.html.corrected.txt",
                     "r", encoding = "utf-8").read()
print(gold_standard)
root.z = 5
print(type(root.z))
lber = LCSLabeler(root, gold_standard)
lber.DFT_driver()
for pre, _, node in RenderTree(root):
    treestr = u"%s%s" % (pre, node.name)
    m = getattr(node, "matches", "")
    c = getattr(node, "DOM_features", "")["n_char"]
    print(treestr.ljust(8), m/c if c!=0 else m, m, c)