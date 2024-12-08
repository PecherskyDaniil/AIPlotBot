from selenium import webdriver
from selenium.webdriver.common.by import By
from random import randint
from time import sleep
from selenium.webdriver import ActionChains
# set up options to configure Chrome

def init_webdriver():
    options = webdriver.ChromeOptions()
    # run in headless mode (no GUI)
    options.add_argument("--headless=new")
    # set window size
    options.add_argument("--window-size=1920x1080")
    # initialize the WebDriver with the specified options
    driver = webdriver.Chrome(options=options)
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
def get_screenshot(dashboard_id,filter_state,filename,driver):
    # navigate to the target website
    driver.get("http://localhost:8088/superset/dashboard/"+str(dashboard_id)+"/?native_filters_key="+filter_state+"&standalone=true")
    hidebutton=driver.find_element(By.CSS_SELECTOR, 'button[class="ant-btn superset-button superset-button-link css-15fnute"')
    hidebutton.click()
    sleep(10)
    hoverable = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Edit dashboard"]')
    ActionChains(driver).move_to_element(hoverable).perform()
    driver.execute_script("document.body.style.zoom='45%'")
    sleep(2)
    print("Taking screenshot...")
    # take a screenshot and save it to a file
    driver.save_screenshot(filename)
    print("Screenshot taken successfully.")
    # clean up and close the browser
    

