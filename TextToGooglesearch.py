# Python program to automate analyst Google Searches
# Currently on Chrome and ChromeDriver versions 113
#Stuff I'm using:
#Selenium browser automation https://www.selenium.dev/
#A ChromeDriver manager https://pypi.org/project/webdriver-manager/
#A Selenium screenshot package https://pypi.org/project/Selenium-Screenshot/

#Chrome folder: C:\Program Files\Google\Chrome\Application

# import webdriver, Service, Options, webdrivermanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from Screenshot import Screenshot

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
# add the Google Search URL prefix, replace any spaces with a plus sign, and put the result into a new list
URL_List = []
for i in range(len(TermsList)):
    URL = "https://www.google.com/search?q=" + TermsList[i].replace(" ", "+")
    URL_List.append(URL)

#set output path
pdf_file_path = r"C:\Users\mattn\Life\Coding\OutputDump"
#Set options to headless mode and pdf printing for Chrome webdriver instance
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument("--window-size=1600,1000")
#chrome_options.add_argument('--disable-print-preview')
#chrome_options.add_argument('--print-to-pdf=' + pdf_file_path)
#chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

#specify chromedriver.exe path
driver_path = r"C:\Users\mattn\Life\Coding\ChromeDriver\chromedriver.exe"
#init driver
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

print("Did I make it here?")

ob = Screenshot.Screenshot()
#Loop through our list using driver.get() to pull the webpages
#Hopefully this prints to pdf
for i in range(len(URL_List)):
    #Bring up the Google Search
    driver.get(URL_List[i])

    #Remove the searchbar that stays at the top of the screen, blocks info further down.
    #This also makes it so that you can't technically see what was searched apart from the filename. RIP.
    search_bar = driver.find_element_by_xpath('//*[@id="searchform"]')
    driver.execute_script("""var element = arguments[0]; element.parentNode.removeChild(element);""", search_bar)
    #Take screenshot
    img_url = ob.full_screenshot(driver, save_path=pdf_file_path, image_name=("www_" + TermsList[i] + "_Google Search_" + date + ".pdf"), is_load_at_runtime=True, load_wait_time=3)                             

#Ragequit
driver.quit()
#The Print button is not part of the DOM

print("Did I make it here2?")
input('Press ENTER to exit')
