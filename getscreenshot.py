from selenium import webdriver
from selenium.webdriver.common.by import By
from random import randint
from time import sleep
from selenium.webdriver import ActionChains
import os

# set up options to configure Chrome

def init_webdriver():
    options = webdriver.ChromeOptions()
    relative_download_path = "./images"  # Относительный путь
    absolute_download_path = os.path.abspath(relative_download_path)
    options.add_experimental_option('prefs', {
    'download.default_directory': absolute_download_path,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
})
    # run in headless mode (no GUI)
    options.add_argument("--headless=new")
    # set window size
    options.add_argument("--window-size=1920x1080")
    options.add_argument("window-size=1920,1080")
    # initialize the WebDriver with the specified options
    driver = webdriver.Chrome(options=options)
    print(webdriver)
    driver.implicitly_wait(10)
    driver.get('http://localhost:8088/login/')
    username_input = driver.find_element(By.CSS_SELECTOR, 'input[name="username"]')
    password_input = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    username_input.send_keys("admin")
    password_input.send_keys("admin")
    login_button = driver.find_element(By.XPATH, '//input[@type="submit"]')
    login_button.click()
    sleep(5)
    return driver
def get_screenshot(chart_id,filename,driver):
    # navigate to the target website
    driver.get("http://localhost:8088/explore/?slice_id="+str(chart_id))
    #hidebutton=driver.find_element(By.CSS_SELECTOR, 'button[class="ant-btn superset-button superset-button-link css-15fnute"')
    #hidebutton.click()
    #sleep(10)
    #driver.execute_script("document.body.style.zoom='45%'")
    hidebutton=driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Menu actions trigger"')
    hidebutton.click()
    sleep(5)
    downloadbuttton=driver.find_element(By.CSS_SELECTOR, 'div[title=\"Download\"]')
    downloadbuttton.click()
    sleep(15)
    downloadimagebut=driver.find_element(By.XPATH,"//*[contains(text(), 'Download as image')]")
    downloadimagebut.click()
    sleep(10)
    os.rename("./images/"+os.listdir("./images")[0],filename)
    #hoverable = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Edit dashboard"]')
    #ActionChains(driver).move_to_element(hoverable).perform()
    
    #sleep(2)
    print("Taking screenshot...")
    # take a screenshot and save it to a file
    #driver.save_screenshot(filename)
    print("Screenshot taken successfully.")
    # clean up and close the browser
    

