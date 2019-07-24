from anytree.importer import JsonImporter
from anytree import RenderTree
import threading

def DFT(node):
    for Cnode in node.children:
        Cnode_thread = threading.Thread(target = DFT, args = (Cnode,))
        Cnode_thread.start()
        Cnode_thread.join()
    print(node.name)
importer = JsonImporter()
root = importer.read(open("D:\\Downloads\\featuresTree_test.json", encoding="utf-8"))
DFT(root)