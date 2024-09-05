import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import os


#function to pull publication title
def get_publication_title(driver, xpath):
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return title_element.text.strip()
    except Exception as e:
        print(f"Error getting publication title: {str(e)}")
        return "Unknown_Publication"

#function to sanitize file name
def sanitize_filename(filename):
    # Remove or replace characters that are invalid in file names
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

#function to download newspaper pages
def download_newspaper_pages(url):
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Get the publication title and create a sanitized folder name
    publication_title = get_publication_title(driver, './/div[@id="item-cataloged-data"]//ul[@aria-labelledby="item-title"]/li') 
    folder_name = sanitize_filename(publication_title)
    
    # Create the folder
    download_folder = os.path.join(os.getcwd(), "downloads", folder_name)
    os.makedirs(download_folder, exist_ok=True)

    # Update Chrome options with the new download directory
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(os.getcwd(), download_folder),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    # Restart the browser with the new options
    driver.quit()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    while True:
        try:
            # Wait for the page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "download")))

            # Find the dropdown element
            dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "page"))
            )

            # Get current page number
            current_page = dropdown.find_element(By.CSS_SELECTOR, "option[selected]").get_attribute("value")
            print(f"Downloading page {current_page}")

            # Find and click the download button
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, './/div[@class="files input-group-small"]//button[@type="submit"]'))
            )
            download_button.click()

            # Wait for the download to complete
            time.sleep(5)

            # Rename the downloaded file
            downloaded_files = [f for f in os.listdir(download_folder) if f.endswith('.pdf')]
            if downloaded_files:
                latest_file = max(downloaded_files, key=lambda f: os.path.getmtime(os.path.join(download_folder, f)))
                new_file_name = f"page_{current_page}.pdf"
                os.rename(os.path.join(download_folder, latest_file), os.path.join(download_folder, new_file_name))

            # Find and click the "next" button
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "next")]'))
            )
            next_button.click()

            # Wait for the page to reload
            time.sleep(2)

        except StaleElementReferenceException:
            print("Page reloaded, retrying...")
            continue
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            break

    driver.quit()

# Usage
newspaper_url = "https://www.loc.gov/resource/sn96086912/1882-10-07/ed-1/?sp=1&st=image"
download_newspaper_pages(newspaper_url)