from os import listdir
from os.path import isfile, join
from selenium import webdriver
import FeaturesTree as ft
from anytree.exporter import JsonExporter
import datetime

if __name__ == '__main__':
    #get all webpage
    #path = "D:/Downloads/dragnet_data-master/HTML"
    #files = [f for f in listdir(path) if isfile(join(path, f))]
    #read previous session
    with open("D:/Downloads/browserSession.txt", "r") as f:
        executor_url = f.readline()
        session_id = f.readline()        
        f.close()
    #browser options
    options = webdriver.ChromeOptions()
    options.add_argument('-headless')        
    driver = webdriver.Remote(command_executor=executor_url,
                              desired_capabilities={},
                              options = options)
    #close new opened windows
    driver.close()
    #attach to exist browser
    driver.session_id = session_id
    print(driver.command_executor._url)
    print(driver.session_id)
    #get webpage
    driver.get("file:///D:/Downloads/dragnet_data-master/HTML/test.html")
    print(driver.current_url)
    #start parsing
    str_cvrt = datetime.datetime.now()
    ftree = ft.FeaturesTree(driver.find_element_by_tag_name("html"), driver, 
                            "D:\\Downloads\\top_100_fonts_lowercase.csv", 
                            "./returnChildNodes.js")
    root = ftree.DFT_driver()
    #print as tree format
    #ftree.printTree(root)
    #print as JSON format
    end_cvrt = datetime.datetime.now()
    exporter = JsonExporter(indent=2)
    print(exporter.export(root))
    #print duration time
    print(end_cvrt - str_cvrt)