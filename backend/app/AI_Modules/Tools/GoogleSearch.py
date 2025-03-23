from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import logging
import traceback
from urllib.parse import quote_plus
import os
from datetime import datetime

if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"google_search_log_{current_time}.log")

logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class GoogleSearchAutomator:
    def __init__(self,debug=False):
        self.debug = debug
        self.html_output_dir = "html_debug"
        os.makedirs(self.html_output_dir, exist_ok=True)
        if not os.path.exists('results'):
            os.makedirs('results')
        logging.info("Initializing GoogleSearchAutomator")

    def _save_html_page(self, html_content, query, page_number):
        """Save HTML content to file for debugging"""
        try:
            safe_query = "".join([c if c.isalnum() else "_" for c in query])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.html_output_dir}/{safe_query}_{page_number}_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"Saved HTML page: {filename}")
        except Exception as e:
            logging.error(f"Failed to save HTML: {str(e)}")

    def _create_driver(self,headless=True):
        """Create a new driver instance with randomized settings"""
        try:
            
            window_sizes = [
                (1280, 800), (1366, 768), (1440, 900), (1536, 864), (1600, 900),
                (1920, 1080), (1280, 720), (1024, 768)
            ]
            
            chosen_window_size = random.choice(window_sizes)
            
            driver_options = {
                "uc": True,             
                "headless": headless,      
            }
            
            driver = None
            for attempt in range(3):
                try:
                    driver = Driver(**driver_options)
                    break
                except Exception as e:
                    logging.warning(f"Driver creation attempt {attempt+1} failed: {str(e)}")
                    time.sleep(2)
                    
            if driver is None:
                raise Exception("Failed to create driver after multiple attempts")
            
            try:
                driver.set_window_size(chosen_window_size[0], chosen_window_size[1])
            except Exception as e:
                logging.warning(f"Failed to set window size: {str(e)}, continuing anyway")
            
            try:
                driver.set_page_load_timeout(30)
                driver.implicitly_wait(10)
            except Exception as e:
                logging.warning(f"Failed to set timeouts: {str(e)}, continuing anyway")
            
            logging.info(f"Created new driver with window size: {chosen_window_size}")
            return driver
        
        except Exception as e:
            logging.error(f"Failed to create driver: {str(e)}")
            traceback.print_exc()
            return None

    def search_google(self, query, pages=2, scholar=False):
        """Perform a Google search and extract all search result links"""
        results = []
        driver = None
        
        for attempt in range(3):
            try:
                driver = self._create_driver()
                if not driver:
                    logging.error("Failed to create driver, retrying...")
                    time.sleep(2)
                    continue
                    
                base_url = "https://scholar.google.com/" if scholar else "https://www.google.com/"
                
                logging.info(f"Navigating to {base_url}")
                driver.get(base_url)
                wait_time = 2 + random.random() * 2
                time.sleep(wait_time)
                
                self._handle_consent_and_cookies(driver)
                
                logging.info(f"Entering search query: {query}")
                try:
                    search_box = driver.find_element(By.NAME, "q")
                    search_box.clear()
                    search_box.send_keys(query)
                    search_box.send_keys(Keys.RETURN)
                except:
                    encoded_query = quote_plus(query)
                    search_url = f"{base_url}search?q={encoded_query}&hl=en"
                    logging.info(f"Navigating directly to search URL: {search_url}")
                    driver.get(search_url)
                
                wait_time = 2 + random.random() * 2
                logging.info(f"Waiting {wait_time:.2f}s for search results to load")
                time.sleep(wait_time)
                
                for page_num in range(1, pages + 1):
                    logging.info(f"Processing page {page_num}")
                    
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "search"))
                        )
                    except:
                        logging.warning("Search results element not found, continuing anyway")
                    
                    html_content = driver.page_source
                    if self.debug:
                        self._save_html_page(html_content, query, page_num)
                    
                    page_results = self._parse_results(html_content)
                    
                    for result in page_results:
                        if result not in results:
                            results.append(result)
                    
                    logging.info(f"Found {len(page_results)} results on page {page_num}")
                    
                    if page_num < pages:
                        try:
                            next_button = driver.find_element(By.ID, "pnnext")
                            next_button.click()
                            logging.info(f"Navigated to page {page_num + 1}")
                            wait_time = 2 + random.random() * 3
                            logging.info(f"Waiting {wait_time:.2f}s for next page")
                            time.sleep(wait_time)
                        except Exception as e:
                            logging.warning(f"Could not navigate to next page: {str(e)}")
                            break
                if self.debug:
                    self._save_results_to_file(query, results)
                
                break
                
            except Exception as e:
                logging.error(f"Search attempt {attempt+1} failed: {str(e)}")
                
            finally:
                if driver:
                    try:
                        driver.quit()
                        logging.info("Driver closed successfully")
                    except:
                        logging.warning("Error closing driver")
        
        return results
    
    def _save_results_to_file(self, query, results):
        """Save search results to a text file"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            query_slug = query.replace(' ', '_').lower()[:20]
            links_filename = os.path.join('results', f"{query_slug}_{current_time}.txt")
            
            with open(links_filename, 'w', encoding='utf-8') as file:
                for result in results:
                    file.write(f"{result['link']}\n")
            
            logging.info(f"Saved {len(results)} links to {links_filename}")
        except Exception as e:
            logging.error(f"Error saving results to file: {str(e)}")
    
    def _handle_consent_and_cookies(self, driver):
        """Handle any consent or cookie dialogs that might appear"""
        try:
            consent_selectors = [
                "button#L2AGLb", 
                "div.J2QUgc button", 
                "form[action*='consent'] button", 
                "button[aria-label*='consent']",
                "button[jsname='higCR']",
                "//button[contains(., 'Accept all')]",
                "//button[contains(., 'I agree')]",
                "//button[contains(., 'Agree')]"
            ]
            
            for selector in consent_selectors:
                try:
                    if selector.startswith("//"):
                        consent_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        consent_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    time.sleep(random.uniform(0.5, 1.5))
                    consent_button.click()
                    logging.info(f"Clicked consent button with selector: {selector}")
                    time.sleep(random.uniform(1, 2))
                    return
                except:
                    continue
                    
        except Exception as e:
            logging.info(f"No consent dialogs found or error handling them: {str(e)}")
    
    def _parse_results(self, html_content):
        """Parse search results from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        selectors = [
            "div.g .yuRUbf a",
            "div.tF2Cxc .yuRUbf a",
            "div.g a[href^='http']",
            "div.MjjYud a[jsname='UWckNb']",
            'div[data-header-feature="0"] a[href^="http"]',
            'div.g:not(.g-blk) a[href^="http"]',
            'div[data-snf] a[href^="http"]',
            'a[jsname="UWckNb"]',
            'div[jsname="NokBGb"] a[href^="http"]'
        ]
        
        for selector in selectors:
            search_results = soup.select(selector)
            if search_results:
                logging.info(f"Found {len(search_results)} results with {selector}")
                for result in search_results:
                    try:
                        href = result['href']
                        
                        if ('google.com' in href or not href.startswith('http') or 
                            'webcache' in href or 'translate.google' in href):
                            continue
                        
                        title = result.text.strip()
                        if not title and result.find_parent():
                            h3 = result.find_parent().find('h3')
                            if h3:
                                title = h3.text.strip()
                        
                        if not title:
                            title = href
                            
                        result_item = {"title": title, "link": href}
                        if result_item not in results:
                            results.append(result_item)
                    except Exception as e:
                        logging.debug(f"Error parsing result: {str(e)}")
            
        return results