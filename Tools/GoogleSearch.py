import requests
from bs4 import BeautifulSoup
import time
import random
import os
import logging
from datetime import datetime
from urllib.parse import quote_plus

if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_{current_time}.log")

class GoogleSearchAutomator:
    def __init__(self, headless=False):
        # The headless parameter is kept for signature compatibility but isn't used
        logging.info("Initializing GoogleSearchAutomator")
        try:
            logging.info("Creating new Session instance")
            self.session = requests.Session()
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            logging.info("Session instance created successfully")
        except Exception as e:
            logging.error(f"Failed to create Session instance: {str(e)}")
            raise
        
    def human_type(self, element, text):
        """Simulate human typing with random delays - kept for compatibility"""
        # This method isn't needed for requests but kept for signature compatibility
        pass

    def search_google(self, query, pages=1, delay=2, scholar=False):
        results = []
        try:
            base_url = "https://scholar.google.com/scholar" if scholar else "https://www.google.com/search"
            encoded_query = quote_plus(query)
            
            if scholar:
                logging.info("Google scholar search instance made")
            else:
                logging.info("Google search instance made")
            
            # Use a different User-Agent each time
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]
            self.headers['User-Agent'] = random.choice(user_agents)
            
            for page in range(pages):
                start_index = page * 10
                search_url = f"{base_url}?q={encoded_query}&start={start_index}"
                
                # Add random delay for subsequent pages
                if page > 0:
                    sleep_time = delay + random.uniform(-0.5, 0.5)
                    time.sleep(sleep_time)
                
                # Make the request
                logging.info(f"Requesting URL: {search_url}")
                response = self.session.get(search_url, headers=self.headers)
                logging.info(f"Search submitted for query {query}, status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Failed to get search results: Status code {response.status_code}")
                    break
                
                # Save HTML for debugging if needed
                with open(f"search_page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logging.info(f"Saved HTML to search_page_{page}.html for debugging")
                
                # Simulate scrolling (just a log entry for compatibility)
                scroll_amount = random.randint(300, 800)
                logging.info(f"Simulated scroll by {scroll_amount}")
                
                # Parse the results
                page_results = self._parse_results(response.text)
                results.extend(page_results)
                
                logging.info(f"Found {len(page_results)} results on page {page+1}")
                
                if len(page_results) < 10:
                    break
                
                time.sleep(delay * 1.5 + random.uniform(0, 1))
                
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}", exc_info=True)
        
        logging.info(f"Operation finalized, found {len(results)} total results")
        return results

    def _parse_results(self, html_content):
        """Extract search results from HTML content"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Log a small sample of the HTML for debugging
        html_sample = html_content[:500] + "..." if len(html_content) > 500 else html_content
        logging.debug(f"HTML Sample: {html_sample}")
        
        # Try multiple selector patterns that Google might be using
        search_results = []
        
        # Pattern 1: Traditional div.g
        if not search_results:
            search_results = soup.select('div.g')
            logging.info(f"Pattern 1 (div.g) found {len(search_results)} results")
        
        # Pattern 2: More recent structure
        if not search_results:
            search_results = soup.select('div[jscontroller][data-hveid]')
            logging.info(f"Pattern 2 (jscontroller) found {len(search_results)} results")
        
        # Pattern 3: Result container with links
        if not search_results:
            search_results = soup.select('div.tF2Cxc')
            logging.info(f"Pattern 3 (tF2Cxc) found {len(search_results)} results")
        
        # Fallback to any div with a link and header
        if not search_results:
            search_results = [div for div in soup.find_all('div') 
                            if div.find('a') and div.find('h3')]
            logging.info(f"Pattern 4 (fallback) found {len(search_results)} results")
        
        for result in search_results:
            try:
                # Try to find the link - Google often has multiple <a> tags
                link_element = None
                
                # First try direct link under the result
                link_element = result.find('a')
                
                # If not found or not a valid link, try looking deeper
                if not link_element or not link_element.get('href') or not link_element.get('href').startswith('http'):
                    # Try to find deeper nested links
                    deeper_links = result.select('a[href^="http"]')
                    if deeper_links:
                        link_element = deeper_links[0]
                
                if not link_element or not link_element.get('href'):
                    continue
                    
                link = link_element.get('href')
                
                # Skip non-http links or Google internal links
                if (not link.startswith('http://') and not link.startswith('https://')) or 'google.com' in link:
                    continue
                
                # Try to find the title - look for h3 within the result or near the link
                title_element = result.find('h3')
                if not title_element:
                    # If no h3, try to get the link text
                    title = link_element.get_text().strip()
                else:
                    title = title_element.get_text().strip()
                
                if not title:
                    title = "No title"
                
                results.append({"title": title, "link": link})
                logging.info(f"Found result: {title} - {link}")
                
            except Exception as e:
                logging.info(f"Exception caught while parsing result: {e}")
                continue
        
        return results