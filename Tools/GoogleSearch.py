from seleniumbase import Driver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

class GoogleSearchAutomator:
    def __init__(self, headless=False):
        self.driver = webdriver(uc=True,headless=headless)

    def human_type(self,element, text):
        """Simulate human typing with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.3))

    def search_google(self, query, pages=1, delay=2):
        results = []
        try:
            self.driver.get("https://www.google.com")
            # For the cookies 
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "L2AGLb"))
                ).click()
            except:
                pass

            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="APjFqb"]'))
            )
            self.human_type(search_box, query)
            search_box.submit()
            
            for _ in range(pages):
                time.sleep(delay + random.uniform(-0.5, 0.5))
                
                # Scroll randomly
                self.driver.execute_script(
                    f"window.scrollBy(0, {random.randint(300, 800)})")
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
                )
                results += self._parse_results()
                
                try:
                    next_btn = self.driver.find_element(
                        By.CSS_SELECTOR, "#pnnext")
                    next_btn.click()
                except:
                    break  
                
                time.sleep(delay * 1.5 + random.uniform(0, 1))
                
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self.driver.quit()
        
        return results

    def _parse_results(self):
        """Extract search results with multiple selectors"""
        results = []
        for result in self.driver.find_elements(By.CSS_SELECTOR, "div.g"):
            try:
                link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                results.append({"title": title, "link": link})
            except:
                continue
        return results

