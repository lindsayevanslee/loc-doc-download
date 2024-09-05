import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
import os
import json

def get_publication_info(driver, xpath, item_description):
    try:
        # Wait for the title element to be present
        info_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return info_element.text.strip()
    except Exception as e:
        print(f"Error getting publication {item_description}: {str(e)}")
        return f"Unknown_{item_description}"

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'  # Invalid characters for a filename
    for char in invalid_chars:
        filename = filename.replace(char, '_')  # Replace invalid characters with underscores
    return filename

def extract_and_save_metadata(driver, download_folder):
    try:
        # Find the metadata div
        metadata_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "item-cataloged-data"))
        )
        
        metadata = {}
        h3_elements = metadata_div.find_elements(By.TAG_NAME, "h3")
        
        for h3 in h3_elements:
            title = h3.text.strip()
            ul = h3.find_element(By.XPATH, "following-sibling::ul[1]")
            li_elements = ul.find_elements(By.TAG_NAME, "li")
            
            if len(li_elements) == 1:
                metadata[title] = li_elements[0].text.strip()
            else:
                metadata[title] = [li.text.strip() for li in li_elements]
        
        # Save metadata as JSON
        with open(os.path.join(download_folder, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        print("Metadata saved successfully.")
    except Exception as e:
        print(f"Error extracting metadata: {str(e)}")
        

def download_newspaper_pages(url):
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    while True:  # Main loop to cycle through all issues
        # Get the publication title and date and sanitize it to use as a folder name
        #publication_title = get_publication_info(driver, './/div[@id="item-cataloged-data"]//ul[@aria-labelledby="item-title"]/li', "title")
        publication_title = get_publication_info(driver, './/div[@id="part-of"]//ul[@aria-labelledby="item-facet-part-of"]/li[1]/a', "title")
        publication_date = get_publication_info(driver, './/div[@id="facets-box"]//ul[@aria-labelledby="item-facet-dates"]/li/a', "date")
        

        print(f"Downloading pages of {publication_title} - {publication_date}")
        
        folder_name = sanitize_filename(publication_title) + "/" + sanitize_filename(publication_date)
        
        download_folder = os.path.join(os.getcwd(), "downloads", folder_name)
        os.makedirs(download_folder, exist_ok=True)

        # Extract and save metadata
        extract_and_save_metadata(driver, download_folder)

        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        driver.quit()
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        while True:  # Inner loop for pages within an issue
            try:
                # Wait for the download button to be present
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "download")))

                dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "page"))
                )

                current_page = dropdown.find_element(By.CSS_SELECTOR, "option[selected]").get_attribute("value")
                print(f"Downloading page {current_page}")

                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, './/div[@class="files input-group-small"]//button[@type="submit"]'))
                )
                download_button.click()

                time.sleep(5)

                downloaded_files = [f for f in os.listdir(download_folder) if f.endswith('.pdf')]
                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda f: os.path.getmtime(os.path.join(download_folder, f)))
                    new_file_name = f"page_{current_page}.pdf"
                    os.rename(os.path.join(download_folder, latest_file), os.path.join(download_folder, new_file_name))

                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "next")]'))
                )
                next_button.click()

                time.sleep(2)

            except StaleElementReferenceException:
                print("Page reloaded, retrying...")
                continue
            except NoSuchElementException:
                print("Reached the last page of the current issue.")
                break
            except Exception as e:
                print(f"An error occurred while downloading pages: {str(e)}")
                break

        # After finishing all pages of the current issue, try to move to the next issue
        try:
            # Look for the "Next issue" button
            next_issue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@aria-labelledby, "next issue")]'))
            )
            next_issue_button.click()
            print("Moving to the next issue...")
            time.sleep(5)  # Wait for the new issue page to load
            url = driver.current_url  # Update the URL for the next iteration
        except TimeoutException:
            print("No more issues available. Finished downloading all issues.")
            break
        except Exception as e:
            print(f"An error occurred while moving to the next issue: {str(e)}")
            break

    driver.quit()

# URL of first page of first issue
newspaper_url = "https://www.loc.gov/resource/sn96086912/1882-10-07/ed-1/?sp=1&st=image"
download_newspaper_pages(newspaper_url)


#TODO:
#try again if a page doesn't download properly
#also download the OCR text