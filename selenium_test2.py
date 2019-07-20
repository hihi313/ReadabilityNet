from os import listdir
from os.path import isfile, join
from selenium import webdriver
import FeaturesTree as ft
from anytree.exporter import JsonExporter
import re

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
    node = driver.find_element_by_css_selector("body > h2")
    print(node.tag_name, 'color:', node.value_of_css_property('color'))
    num_regex = "[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    print([float(x[0]) for x in re.findall(num_regex, node.value_of_css_property('color'))])
    print(node.tag_name, 'line-height:', node.value_of_css_property('line-height'))
    print(node.tag_name, 'font-family:', node.value_of_css_property('font-family'))
    arr = ["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "emoji", "math", "fangsong"]
    font_regex = "(serif|sans\-serif|monospace|cursive|fantasy|system\-ui|emoji|math|fangsong)$"
    tmp = re.search(font_regex, node.value_of_css_property("font-family")).group(0)
    print([1 if x==tmp else 0 for x in arr])
    print(node.tag_name, 'margin:', node.value_of_css_property('margin'))
    print(node.tag_name, 'padding:', node.value_of_css_property('padding'))
    print(node.tag_name, 'border-width:', node.value_of_css_property('border-width'))
    print(node.tag_name, 'rect:', node.rect)
    print(node.tag_name, 'display:', node.value_of_css_property('display'))
    d_tmp = node.value_of_css_property('display')
    disp = ["inline", "block", "contents", "flex", "grid", "inline-block", "inline-flex", "inline-grid",
            "inline-table", "list-item", "table", "table-caption", "table-column-group", "table-header-group",
            "table-footer-group", "table-row-group", "table-cell", "table-column", "table-rownone"]
    display = [1 if d==d_tmp else 0 for d in disp]
    print(display)
    print(node.tag_name, 'visibility:', node.value_of_css_property('visibility'))
    print(node.tag_name, 'is_displayed:', node.is_displayed())
    print(1 if node.is_displayed() else 0)
    #ftree = ft.FeaturesTree(driver.find_element_by_tag_name("html"), driver)
    #root = ftree.DFT_driver()
    #ftree.printTree(root)
    #print as JSON format
    #exporter = JsonExporter(indent=2)
    #print(exporter.export(root))
    #driver.close()
    