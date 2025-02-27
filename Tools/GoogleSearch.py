import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from urllib.parse import quote_plus

class GoogleSearchAutomator:
    def __init__(self):
        logging.info("Initializing GoogleSearchAutomator")
        try:
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

    def search_google(self, query, pages=1, delay=2, scholar=False):
        results = []
        try:
            base_url = "https://scholar.google.com/scholar" if scholar else "https://www.google.com/search"
            encoded_query = quote_plus(query)
            
            logging.info(f"{'Google scholar' if scholar else 'Google'} search instance made for query: {query}")
            
            # Rotate user agents for each request to avoid being blocked
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ]
            
            for page in range(pages):
                # Update user agent for each request
                self.headers['User-Agent'] = random.choice(user_agents)
                
                start_index = page * 10
                search_url = f"{base_url}?q={encoded_query}&start={start_index}"
                
                # Add delay between pages (but not for the first page)
                if page > 0:
                    sleep_time = delay + random.uniform(-0.5, 0.5)
                    time.sleep(sleep_time)
                
                # Make the request
                logging.info(f"Requesting URL: {search_url}")
                response = self.session.get(search_url, headers=self.headers)
                logging.info(f"Search response received, status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Failed to get search results: Status code {response.status_code}")
                    break
                
                # Parse the results
                page_results = self._parse_results(response.text)
                results.extend(page_results)
                
                logging.info(f"Found {len(page_results)} results on page {page+1}")
                
                # If we got fewer results than expected, we've reached the end
                if len(page_results) < 10:
                    break
                
                # Add variable delay between pages to appear more human-like
                if page < pages - 1:
                    time.sleep(delay + random.uniform(0, 1))
                
        except Exception as e:
            logging.error(f"Error occurred during search: {str(e)}", exc_info=True)
        
        logging.info(f"Search completed, found {len(results)} total results")
        return results

    def _parse_results(self, html_content):
        """Extract search results from HTML content"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"page_{timestamp}_{random.randint(1, 1000)}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"Saved HTML content to {filename}")
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
                # Try to find the link
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
                logging.info(f"Found result: {title[:30]}... - {link}")
                
            except Exception as e:
                logging.info(f"Exception caught while parsing result: {e}")
                continue
        
        return results