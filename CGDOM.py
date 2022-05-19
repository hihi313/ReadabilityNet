htmlPath = "D:/Downloads/dragnet_data-master/HTML/"
jsonPath = "D:/Downloads/dragnet_data-master/JSON/"
files = []
for f in listdir(jsonPath):
    p = join(jsonPath, f)
    if isfile(p) and f.endswith(".json"):
        files.append(p)
# sort by size
files = sorted(files, key=os.path.getsize)
# initialize & get common used variables
com = LabelerVars(debug=debug)

jsons = ["109.json"]
files = [jsonPath + j for j in jsons]

threads = [] # child threads
shift = 5
start = 0
end = start + shift
while(files[start:end]):            
    for f in files[start:end]:
        # check whether the file has been processed
        fName = re.sub("[\s\S]*[\\/]", '', re.sub("\.[\s\S]*", '', f))
        if not os.path.exists(labeledPath + fName + fileName_suffix + ".json"):
            print("processing:", jsonPath + fName + ".json")
            thread = threading.Thread(target=labelAPage, args=(com, fName))
            thread.start()
            threads.append(thread)
        else:
            print("skip:", f)
    for t in threads:
        t.join()
    start = end
    end += shift

print("done")
