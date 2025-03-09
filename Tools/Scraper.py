import requests
from bs4 import BeautifulSoup
import pandas as pd
import json     
from typing import List, Dict
from Utils.Model import Model    
import re
import urllib3
from urllib.parse import urljoin, urlparse
import os 
import logging
from datetime import datetime


if not os.path.exists('logs'):
    os.makedirs('logs')


current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_{current_time}.log")

logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Scrapy:
    """AI powered scraping class"""
    
    def __init__(self,base_url:str,model:Model):
        self.header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = base_url
        logging.info(f"Initializing scrapy for {self.base_url}")
        self.sub_sites = []
        self.visited_sites = set()
        self.scraped_page = []
        self.model = model
        logging.info("Scrapy initialization complete")
        
    def _extract_content(self, soup:BeautifulSoup):
        """Extract main content from HTML soup, removing noise elements"""
        for element in soup.select('header, footer, nav, script, style, [class*="menu"], [class*="sidebar"], [class*="banner"], [class*="ad"], [id*="ad"], [class*="cookie"], [class*="popup"]'):
            element.decompose()
        
        content_containers = [
            soup.find('main'),
            soup.find('article'),
            soup.find('div', class_=re.compile(r'content|main|article|post|entry')),
            soup.find('div', id=re.compile(r'content|main|article|post|entry')),
            soup.select_one('.content, .main, .article, .post, .entry'),
            soup.select_one('#content, #main, #article, #post, #entry')
        ]
        
        for container in content_containers:
            if container:
                content = container.get_text(separator=' ', strip=True)
                content = re.sub(r'\s+', ' ', content).strip()
                return content
                
        body = soup.find('body')
        if body:
            content = body.get_text(separator=' ', strip=True)
            content = re.sub(r'\s+', ' ', content).strip()
            return content
            
        return soup.get_text(separator=' ', strip=True)

    def _is_valid_url(self,url:str):
        try:
            parsed = urlparse(url)
            base_domain = urlparse(self.base_url).netloc.replace('wwww.','')
            current_domain = parsed.netloc.replace('wwww.','')
            
            if base_domain != current_domain:
                return False 

            excluded_domains = [
                'linkedin.com', 'facebook.com','x.com',
                'instagram.com', 'youtube.com'
            ]
            
            if any(domain in parsed.netloc.lower() for domain in excluded_domains):
                logging.info("Removing socials links")
                return False
            
            return True 
        except Exception as e:
            logging.info(f"Exception {e} has occured while validating url for base url {base_domain} and target {current_domain}")
            return False
        
        
    def dismantle_webpage(self,url:str,user_prompt:str="",get_sublinks = False):
        """
        user_prompt : Parameter for the user to specify the goal of the scraping the website / webpage
        """
        try:
            response = requests.get(url)
            self.visited_sites.add(url)
            body = response.content
            soup = BeautifulSoup(body,'html.parser')
            title = soup.title.string if soup.title else "No title found"
            content = self._extract_content(soup)
            page_data = {
                'title': title,
                'url' : url,
                'content': content
            }
            self.scraped_page.append(page_data)
            if get_sublinks:
                links = []
                for link in soup.find_all('a',href=True):
                    full_url = urljoin(url,link['href'])
                    if self._is_valid_url(full_url):
                        links.append(full_url)
                if links:
                    links = self.sub_link_filter(links,user_prompt)
                    for link in links:
                        if link not in self.visited_sites:
                            self.sub_sites.append(link)
            
        except Exception as e:
            logging.info(e)
            
    def dismantle_website(self,user_prompt):
        self.dismantle_webpage(self.base_url,user_prompt)
        while self.sub_sites:
            page = self.sub_sites.pop()
            self.dismantle_webpage(page,user_prompt)
            
            
    
    def sub_link_filter(self,links:List[str],user_prompt:str=""):
        prompt = f"""From this list of links {links} and this {self.base_url} 
                    remove the links that you do not think will contain relevant data,
                    also remove the links of social media accounts.
                    Only keep valid web links, links that are directly related to {self.base_url} and serve the purpose for {user_prompt}
                    Make sure to keep only the links that could contain valuable information about the website.
                    Return the data as a json like this {{"valuable_links":["list of links to keep"]}}"""
        try:
            model_response = self.model._run(prompt)
        except Exception as e:
            logging.info(e)
        try:
            start_idx = model_response.find('{')
            end_idx = model_response.rindex('}')+1
            json_str = model_response[start_idx:end_idx]
            valid_links = json.loads(json_str)
            logging.info(valid_links)
            final_links = valid_links.get("valuable_links") or []
            return final_links
        
        except Exception as e:
            logging.info(e)
    
    def save_to_csv(self,file_name='website_as_csv'):
        if not self.scraped_page:
            logging.info("No content found")
            return 
        df = pd.DataFrame(self.scraped_page)
        df.to_csv(file_name,index=False,encoding='utf-8')