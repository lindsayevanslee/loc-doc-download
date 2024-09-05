import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

def download_newspaper_pages(url):

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(os.getcwd(), "newspaper_pdfs"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    # Setup Selenium WebDriver with the new options
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)


    # Wait for the page to load - waits for the download button to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "download")))
    
    # Find the dropdown element
    dropdown = driver.find_element(By.ID, "page")
    
    # Get all options from the dropdown
    options = dropdown.find_elements(By.TAG_NAME, "option")
    
    # Create a directory to store the PDFs
    os.makedirs("newspaper_pdfs", exist_ok=True)
    
    # Iterate through all pages
    for option in options:
        page_number = option.get_attribute("value")
        print(f"Downloading page {page_number}")
        
        # Select the page
        option.click()
        
        # Find and click the "go" button to select next page
        go_button = driver.find_element(By.XPATH, './/div[@id="other-viewer-controls"]//button[@type="submit"]')
        go_button.click()
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "download")))
        
        # Find and click the download button
        download_button = driver.find_element(By.XPATH, './/div[@class="files input-group-small"]//button[@type="submit"]')
        download_button.click()
        
        # Wait for the download to complete (you may need to adjust the wait time)
        time.sleep(5)
        
        # The file should now be in the newspaper_pdfs directory with its original name
        # You may want to rename it to match your desired format
        downloaded_files = [f for f in os.listdir("newspaper_pdfs") if f.endswith('.pdf')]
        if downloaded_files:
            latest_file = max(downloaded_files, key=lambda f: os.path.getmtime(os.path.join("newspaper_pdfs", f)))
            new_file_name = f"page_{page_number}.pdf"
            os.rename(os.path.join("newspaper_pdfs", latest_file), os.path.join("newspaper_pdfs", new_file_name))

    
    driver.quit()

# Usage
newspaper_url = "https://www.loc.gov/resource/sn96086912/1882-10-07/ed-1/?sp=1&st=image"
download_newspaper_pages(newspaper_url)