from anytree.importer import JsonImporter
from anytree import RenderTree
import threading, re, time

class LCSLabeler():
    def __init__(self, root, gold_standard):
        self.root = root
        self.rSpace_re = "\s+"
        self.after_comment_re = "!@#\$%\^&\*\(\)\s+COMMENTS[\s\S]*"
        #replace redundant/normalize white space
        tmp_gld = re.sub(self.rSpace_re, " ", gold_standard)
        #replace anything after "!@#$%^&*()  COMMENTS" (remove comment)
        self.gold_standard = re.sub(self.after_comment_re, '', tmp_gld)
    def DFT_driver(self):
        self.DFT(self.root)
    def DFT(self, node):
        #initialize the # matched char 
        tmp_matches = 0
        tmp_nChar = 0       
        for Cnode in node.children:
        ############################################primitive may need to be declare as constant################################################## 
            if Cnode.name == "String":#for text node
                Cnode_thread = threading.Thread(target = self.compare, args = (Cnode,))
            else:#for element node
                Cnode_thread = threading.Thread(target = self.DFT, args = (Cnode,))
            Cnode_thread.start()
            Cnode_thread.join()
            tmp_matches += Cnode.matches
            tmp_nChar += Cnode.DOM_features["n_char"]
        #for element nodes        
        if node.name != "String":
            #matches
            node.matches = tmp_matches
            #similarity
            node.similarity = tmp_matches/tmp_nChar if tmp_nChar != 0 else tmp_matches
    #compare node's string value only for text node
    def compare(self, node):
        txt = re.sub(self.rSpace_re, " ", node.strValue)
        ####################################################primitive need to declare as constant ##########################################
        if len(txt) < 120:#for short string
            #full match
            if re.search(re.escape(txt), self.gold_standard) != None: #match
                node.matches = len(node.strValue)#the length of matched string
            else:
                node.matches = 0
        else:#for long string
            node.matches = self.LCS(txt)
        #similarity
        node.similarity = node.matches/node.DOM_features["n_char"] if node.DOM_features["n_char"] != 0 else node.matches
################################ change to edit distance ? ####################################
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
root = importer.read(open("D:\\Downloads\\R249.json", encoding="utf-8"))
gold_standard = open("D:\\Downloads\\dragnet_data-master\\Corrected\\R249.html.corrected.txt",
                     "r", encoding = "utf-8").read()
#print(gold_standard)
str_cvrt = time.time()
lber = LCSLabeler(root, gold_standard)
lber.DFT_driver()
for pre, _, node in RenderTree(root):
    treestr = u"%s%s" % (pre, node.name)
    print(treestr.ljust(8), getattr(node, "similarity"), getattr(node, "matches"), getattr(node, "DOM_features")["n_char"], getattr(node, "strValue", ''))
end_cvrt = time.time()
print(time.strftime('%H:%M:%S', time.gmtime(end_cvrt - str_cvrt)))