import datetime, threading, re, os
from os import listdir
from os.path import isfile, join

from anytree.exporter import JsonExporter
from selenium import webdriver

import FeaturesTree as ft

def convertAPage(comVar, path):
    # start the browser
    options = webdriver.ChromeOptions()
    options.add_argument("-headless")
    options.add_argument("--window-position=0,0")
    driver = webdriver.Chrome(options = options)
    #set to offline
    driver.set_network_conditions(offline=True, latency=0, 
                                  throughput=1024 * 1024*1024)
    driver.set_window_size(1920, 1080)    
    str_ld = datetime.datetime.now()
    driver.get("file:///" + path)
    # start parsing
    str_cvrt = datetime.datetime.now()
    ftree = ft.FeaturesTree(driver, comVar, debug=False)
    html = driver.find_element_by_tag_name("html")
    root = ftree.DFT_driver(html)
    end_cvrt = datetime.datetime.now()       
    driver.close()
    # export as JSON file
    file_name = re.sub("[\s\S]*[\\/]", '', re.sub("\.[\s\S]*", '', path))
    # print duration time
    print(file_name, "takes:", end_cvrt - str_cvrt, ", load:", str_cvrt - str_ld)
    exporter = JsonExporter(indent=2)
    with open("./JSON/" + file_name + ".json", "w") as f:
        f.write(exporter.export(root))
        f.close()  
    
if __name__ == '__main__':
    # get all webpage
    path = "D:/Downloads/dragnet_data-master/HTML/"
    jsonPath = "D:/OneDrive/Code_Backup/eclipse_workspace/selenium_test2/src/JSON/"
    files = []
    for f in listdir(path):
        p = join(path, f)
        if isfile(p) and f.endswith(".html"):
            files.append(p)
    # sort by size
    files = sorted(files, key=os.path.getsize)
    # initialize & get common used variables
    com = ft.CommonVars("./top_100_fonts_lowercase.csv", 
                         "./returnChildNodes.js", 
                         "./returnNodeAttributes.js",
                         "./jquery.js")
    
    #files = ["D:/Downloads/dragnet_data-master/HTML/509.html"]
    
    threads = [] # child threads
    shift = 5
    start = 0
    end = start + shift
    while(files[start:end]):            
        for f in files[start:end]:
            # check whether the file has been processed
            json = jsonPath + re.sub("[\s\S]*[\\/]", '', 
                                     re.sub("\.[\s\S]*", '', f)) + ".json"
            if not os.path.exists(json):
                print("processing:", f)
                thread = threading.Thread(target=convertAPage, args=(com, f,))
                thread.start()
                threads.append(thread)
            else:
                print("skip:", json)
        for t in threads:
            t.join()
        start = end
        end += shift
    
    print("done")

    '''
    # used for testing
    # read previous session
    with open("./browserSession.txt", "r") as f:
        executor_url = f.readline()
        session_id = f.readline()
        f.close()
    # browser options
    options = webdriver.ChromeOptions()
    options.add_argument('-headless')
    driver = webdriver.Remote(command_executor=executor_url,
                              desired_capabilities={},
                              options=options)
    # close new opened windows
    driver.close()
    # attach to exist browser
    driver.session_id = session_id
    print(driver.command_executor._url)
    print(driver.session_id)
    # get webpage
    driver.get("file:///D:/Downloads/dragnet_data-master/HTML/R249.html")
    print(driver.current_url)    
    # initialize & get common used variables
    vars = ft.CommonVars("./top_100_fonts_lowercase.csv", 
                         "./returnChildNodes.js", 
                         "./returnNodeAttributes.js")
    # start parsing
    debug = False
    print("debug mode:%s" % debug)
    str_cvrt = datetime.datetime.now()
    ftree = ft.FeaturesTree(driver, vars, debug = debug)
    html = driver.find_element_by_tag_name("html")
    root = ftree.DFT_driver(html)
    '''
    # print as tree format
    #ftree.printTree(root)
    '''
    # print as JSON format    
    end_cvrt = datetime.datetime.now()
    exporter = JsonExporter(indent=2)
    print(exporter.export(root))
    # print duration time
    print(end_cvrt - str_cvrt)
    '''
