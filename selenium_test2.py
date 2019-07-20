from os import listdir
from os.path import isfile, join
from selenium import webdriver
import FeaturesTree as ft
from anytree.exporter import JsonExporter

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
    driver.get("file:///D:/Downloads/dragnet_data-master/HTML/test.html")
    print(driver.current_url)
    node = driver.find_element_by_css_selector("body > h1")
    print(node.tag_name, 'color:', node.value_of_css_property('color'))
    print(node.tag_name, 'line-height:', node.value_of_css_property('line-height'))
    print(node.tag_name, 'font-family:', node.value_of_css_property('font-family'))
    print(node.tag_name, 'margin-top:', node.value_of_css_property('margin-top'))
    print(node.tag_name, 'margin-right:', node.value_of_css_property('margin-right'))
    print(node.tag_name, 'margin-bottom:', node.value_of_css_property('margin-bottom'))
    print(node.tag_name, 'margin-left:', node.value_of_css_property('margin-left'))
    print(node.tag_name, 'padding-top:', node.value_of_css_property('padding-top'))
    print(node.tag_name, 'padding-right:', node.value_of_css_property('padding-right'))
    print(node.tag_name, 'padding-bottom:', node.value_of_css_property('padding-bottom'))
    print(node.tag_name, 'padding-left:', node.value_of_css_property('padding-left'))
    print(node.tag_name, 'border-top-width:', node.value_of_css_property('border-top-width'))
    print(node.tag_name, 'border-right-width:', node.value_of_css_property('border-right-width'))
    print(node.tag_name, 'border-bottom-width:', node.value_of_css_property('border-bottom-width'))
    print(node.tag_name, 'border-left-width:', node.value_of_css_property('border-left-width'))
    print(node.tag_name, 'rect:', node.rect)
    print(node.tag_name, 'display:', node.value_of_css_property('display'))
    print(node.tag_name, 'visibility:', node.value_of_css_property('visibility'))
    print(node.tag_name, 'is_displayed:', node.is_displayed())
    #ftree = ft.FeaturesTree(driver.find_element_by_tag_name("html"), driver)
    #root = ftree.DFT_driver()
    #ftree.printTree(root)
    #print as JSON format
    #exporter = JsonExporter(indent=2)
    #print(exporter.export(root))
    #driver.close()
    