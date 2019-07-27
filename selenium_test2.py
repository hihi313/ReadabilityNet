from os import listdir
from os.path import isfile, join
from selenium import webdriver
import FeaturesTree as ft
from anytree.exporter import JsonExporter
import re, time

if __name__ == '__main__':
    path = "D:/Downloads/dragnet_data-master/HTML"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    #print(files)
    #browser options
    options = webdriver.ChromeOptions()
    options.add_argument('-headless')
    #read previous session
    with open("D:/Downloads/browserSession.txt", "r") as f:
        executor_url = f.readline()
        session_id = f.readline()        
        f.close()
    #attach to exist browser    
    driver = webdriver.Remote(command_executor=executor_url,
                              desired_capabilities={},
                              options = options)
    driver.session_id = session_id
    print(driver.command_executor._url)
    print(driver.session_id)
    str_load = time.time()
    driver.get("file:///D:/Downloads/dragnet_data-master/HTML/R249.html")
    print(driver.current_url)
    str_cvrt = time.time()
    ftree = ft.FeaturesTree(driver.find_element_by_tag_name("html"), driver, 
                            "D:\\Downloads\\top_100_fonts_lowercase.csv", "./returnChildNodes.js")
    root = ftree.DFT_driver()
    #ftree.printTree(root)
    #print as JSON format
    end_cvrt = time.time()
    exporter = JsonExporter(indent=2)
    print(exporter.export(root))
    print(time.strftime('%H:%M:%S', time.gmtime(end_cvrt - str_cvrt)))
    #driver.close()
    