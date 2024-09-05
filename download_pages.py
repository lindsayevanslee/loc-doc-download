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

def download_newspaper_pages(url):
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(os.getcwd(), "newspaper_pdfs"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    os.makedirs("newspaper_pdfs", exist_ok=True)

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
            downloaded_files = [f for f in os.listdir("newspaper_pdfs") if f.endswith('.pdf')]
            if downloaded_files:
                latest_file = max(downloaded_files, key=lambda f: os.path.getmtime(os.path.join("newspaper_pdfs", f)))
                new_file_name = f"page_{current_page}.pdf"
                os.rename(os.path.join("newspaper_pdfs", latest_file), os.path.join("newspaper_pdfs", new_file_name))

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
newspaper_url = "https://www.loc.gov/resource/sn96086912/1882-10-07/ed-1/?sp=1&st=image&r=-1.719,-0.087,4.438,1.742,0"
download_newspaper_pages(newspaper_url)