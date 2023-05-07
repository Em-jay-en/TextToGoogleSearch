# Python program to automate analyst Google Searches
# Currently on Chrome and ChromeDriver versions 113

#Chrome folder: C:\Program Files\Google\Chrome\Application

# import webdriver, Service, Options, webdrivermanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

#import datetime
#get the date, stick it in a variable (date)
from datetime import date
today = date.today()
date = today.strftime("%m-%d-%Y")

#Open text file of search terms
SearchList = open("SearchList2.txt", "r")
Terms = SearchList.read()
#Take each term and put it in a list, print to check accuracy
TermsList = Terms.split("\n")
print(TermsList)
#Close file
SearchList.close()
#For each term in the list:
# add the Google Search URL prefix,
# replace any spaces with a plus sign,
# and put the result into a new list
URL_List = []
for i in range(len(TermsList)):
    URL = "https://www.google.com/search?q=" + TermsList[i].replace(" ", "+")
    URL_List.append(URL)
print(URL_List)
print(TermsList)

#pdf_file_path = r"C:\Users\mattn\Life\Coding\OutputDump"
#Set options to headless mode and pdf printing for Chrome webdriver instance
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")
#chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--disable-extensions')
#chrome_options.add_argument('--disable-print-preview')
#chrome_options.add_argument('--print-to-pdf=' + pdf_file_path)
#chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

driver_path = r"C:\Users\mattn\Life\Coding\ChromeDriver\chromedriver.exe"

#I make it here even with options added to webdriver.Chrome() arguments

#driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) [[[THIS NO WORK]]]
#driver = webdriver.Chrome(ChromeDriverManager().install()) [[[THIS WORK MOSTLY]]]

driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

print("Did I make it here?")

#Loop through our list using driver.get() to pull the webpages
#Hopefully this prints to pdf
for i in range(len(URL_List)):
    driver.get(URL_List[i])
    #driver.implicitly_wait(10)
    driver.execute_script("window.print();")
    #Wait until Print Preview loads, then click Print button
  #  wait = WebDriverWait(driver, 10)
  #  element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'action-button')))

    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'action-button')))
    #WebDriverWait.until(EC.presence_of_element_located((By.CLASS_NAME, 'action-button')))
    print_button = driver.find_element(By.CLASS_NAME, 'action-button')
    print_button.click()
    #, ("www_" + TermsList[i] + "_Google Search_" + date + ".pdf")
    #driver.implicitly_wait(100)
print("Did I make it here2?")

#Ragequit
driver.quit()

input('Press ENTER to exit')