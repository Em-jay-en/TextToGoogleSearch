# Python program to automate analyst Google Searches
# Currently on Chrome and ChromeDriver versions 122
#Stuff I'm using:
#Selenium browser automation https://www.selenium.dev/
#A ChromeDriver manager https://pypi.org/project/webdriver-manager/

#Chrome folder: C:\Program Files\Google\Chrome\Application

from selenium import webdriver
import base64
import os
import time

# import GUI library
import tkinter as tk
from tkinter import filedialog

# import datetime
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
root.geometry('400x350')

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
#End of Create User Interface
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
    driver_path = r"C:\Users\mattn\Life\Coding\ChromeDriver\chromedriver-win64\chromedriver.exe"
    #initialize driver
    driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    
    #Replace any invalid characters in the TermsList with an underscore
    def replace_invalid_chars(s):
        invalid_characters = set(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
        return ''.join(char if char not in invalid_characters else '_' for char in s)
    
    # Clean invalid characters from each term in TermsList
    Cleaned_terms = [replace_invalid_chars(term) for term in TermsList]

    #Loop through our list using driver.get() to pull the webpages
    #Hopefully this prints to pdf
    for i in range(len(URL_List)):

        # Formulate the PDF file name based on the current term and date
        pdf_file_name = f"www_{Cleaned_terms[i]}_Google_Search_{date}.pdf"

        # Create the full path by joining the output directory and file name
        full_path = os.path.join(directory, pdf_file_name)

        #Bring up the Google Search
        driver.get(URL_List[i])
        # Sending command to CDP to generate PDF
        result = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "landscape": False,
        # Add other PDF generation options as needed
        })
        # The result is a base64 encoded PDF
        pdf_content = result['data']
        # Decode the PDF and save it to a file
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(pdf_content))
        #Wait 20 seconds every 15 terms to avoid Google throwing to captcha
        if (i + 1) % 15 == 0 and i != len(URL_List) - 1:
            time.sleep(20)    

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
