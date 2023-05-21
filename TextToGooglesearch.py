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

# import GUI library
import tkinter as tk
from tkinter import filedialog

#import datetime
#get the date, stick it in a variable (date), we use this later
from datetime import date
today = date.today()
date = today.strftime("%m-%d-%Y")


def select_file():
    global filename
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        selected_file_label.config(text="Selected file: " + filename)

def select_directory():
    global directory
    directory = filedialog.askdirectory()
    if directory:
        selected_directory_label.config(text="Selected directory: " + directory)

############################################################################
#Create User Interface
root = tk.Tk()
root.title("Text to Google Search PDF")
root.geometry('350x350')

#Create master frame
master_frame = tk.Frame(root)
master_frame.pack(padx=10, pady=10)

#File Selection frame
file_frame = tk.Frame(master_frame)
file_frame.pack(pady=10)

file_button = tk.Button(file_frame, text="Select Text File of Search Terms", command=select_file)
file_button.pack(side=tk.LEFT)

selected_file_label = tk.Label(file_frame, text="Selected file: ")
selected_file_label.pack(side=tk.LEFT, padx=15)
#End File Selection Selection frame

#Output Directory Selection frame
directory_frame = tk.Frame(master_frame)
directory_frame.pack(pady=10)

directory_button = tk.Button(directory_frame, text="Select Output Directory", command=select_directory)
directory_button.pack(side=tk.LEFT)

selected_directory_label = tk.Label(directory_frame, text="Selected directory: ")
selected_directory_label.pack(side=tk.LEFT, padx=15)
#End Output Directory Selection frame

############################################################################

def TextToPDF():
    #Open text file of search terms
    SearchList = open(filename, "r")
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
    pdf_file_path = directory
    #Set options to headless mode and pdf printing for Chrome webdriver instance
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--enable-print-browser')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--window-size=1600,1000")
    chrome_options.add_argument('--log-level=1')
    
    #specify chromedriver.exe path
    driver_path = r"C:\Users\mattn\Life\Coding\ChromeDriver\chromedriver.exe"
    #initialize driver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    
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

    #Success! message
    success_frame = tk.Frame(root)
    success_frame.pack(pady=20)

    selected_file_label = tk.Label(success_frame, text="Success!")
    selected_file_label.pack()
    #End Success! message
    
    root.after(2500, root.destroy)

#Run Button
run_button_frame = tk.Frame(root)
run_button_frame.pack()

run_button = tk.Button(root, text="Run Program", command=TextToPDF)
run_button.pack()
#End Run Button

root.mainloop()
