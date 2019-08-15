from selenium import webdriver

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    ############################################################################ need to set fixed windows size
    #options.add_argument("-headless")
    driver = webdriver.Chrome(options = options)
    #set to offline
    driver.set_network_conditions(offline=True, latency=0, 
                                  throughput=1024 * 1024*1024)
    driver.get("http://www.google.com")
    #save browser session
    executor_url = driver.command_executor._url
    session_id = driver.session_id    
    with open("./browserSession.txt", "w") as f:
        f.write(executor_url)
        f.write("\n")
        f.write(session_id)
        f.close()
    print(session_id)
    print(executor_url)