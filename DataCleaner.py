import os, threading, re
from lxml import html
from lxml.cssselect import CSSSelector

urlLineRegex = "URL:.+"
markupRegex = "\<[phl]\>"
pathRegex = "[\s\S]*[\\/]"
fileExtenRegex = "\.[\s\S]*"

# cleanEval dataset
cleanEvalGoldStd_path = "D:/Downloads/baroni2008cleaneval_dataset/GoldStandard_raw/"
cleanEvalOut_path = "D:/Downloads/baroni2008cleaneval_dataset/cleanEval_goldStandard/"
GoldStd_exten = ".txt"
# Kohlschuetter dataset
KohlschuetterGoldStd_path = "D:/Downloads/Kohlschuetter2010_dataset/Kohlschuetter2010_L3S-GN1-20100130203947-00001/annotated/"
KohlschuetterOut_path = "D:/Downloads/Kohlschuetter2010_dataset/Kohlschuetter2010_L3S-GN1-20100130203947-00001/Kohlschuetter_goldStandard/"
KohlschuetterLabel_XPath = "//text()/parent::*[@class='x-nc-sel1' or @class='x-nc-sel2' or @class='x-nc-sel3']"

printMutex = threading.Lock()

def editCleanEval(fileName, txt):
    try:
        txt = re.sub(markupRegex, '', re.sub(urlLineRegex, '', txt), 
                     flags=re.IGNORECASE)
        with open(cleanEvalOut_path + fileName + GoldStd_exten, "w", 
                  encoding="utf-8") as f:
            f.write(txt)
            f.close()
            with printMutex:
                print("finished:", fileName)
    except BaseException as err:
        with printMutex:
            print("ERROR:", fileName)
        with open(cleanEvalOut_path + "log/ERROR.log", "a", 
                  encoding = 'utf8') as f:
            f.write(u"gstd:%s,\tError:%s\n" % (fileName, err))
            f.close()

def editKohlschuetter(absPath, fileName):
    try:
        doc = html.parse(absPath)
        nodeList = doc.xpath(KohlschuetterLabel_XPath)
        goldStd_txts = [node.text_content() for node in nodeList]
        txt = "\n".join(map(str, goldStd_txts)) 
        with open(KohlschuetterOut_path + fileName + GoldStd_exten, "w", 
                      encoding="utf-8") as f:
                f.write(txt)
                f.close()
                with printMutex:
                    print("finished:", fileName)
    except BaseException as err:
        with printMutex:
            print("ERROR:", fileName)
        with open(KohlschuetterOut_path + "log/ERROR.log", "a", 
                  encoding = 'utf8') as f:
            f.write(u"gstd:%s,\tError:%s\n" % (fileName, err))
            f.close()

files = []
for f in os.listdir(cleanEvalGoldStd_path):
    p = os.path.join(cleanEvalGoldStd_path, f)
    if os.path.isfile(p) and f.endswith(".txt"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
print(len(files))

threads = []
for f in files:
    try:
        txt = open(f, encoding="utf-8", errors="ignore").read()
        fileName = re.sub(pathRegex, '', re.sub(fileExtenRegex, '', f))
        if not os.path.exists(cleanEvalOut_path + fileName + GoldStd_exten):
            print(files.index(f), "processing:", f)
            editThread = threading.Thread(target=editCleanEval, 
                                          args=(fileName, txt,))
            editThread.start()
            threads.append(editThread)
        else:
            print("skip:", f)
    except UnicodeDecodeError as err:
        print(files.index(f), f, "ERROR:", err)
for t in threads:
    t.join()
    
print("done")    