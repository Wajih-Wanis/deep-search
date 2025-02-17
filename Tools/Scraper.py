import requests
from bs4 import BeautifulSoup
import pandas as pd
import json     
from typing import List, Dict
from utils.model import Model    
import os 
import logging
from datetime import datetime


if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_resume_reader_{current_time}.log")

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
        self.sub_sites = []
        self.visited_sites = set()
        self.scraped_page = []
        self.model = model
        
    def dismantle_webpage(self,url,user_prompt):
        """
        user_prompt : Parameter for the user to specify the goal of the scraping the website / webpage
        """
        try:
            response = requests.get(url)
            self.visited_sites.add(url)
            body = response.content
            soup = BeautifulSoup(body,'html.parser')
            title = soup.title.string if soup.title else "No title found"
            if soup.body:
                for irrelevant in soup.body(["script", "style", "img", "input"]):
                    irrelevant.decompose()
                text = soup.body.get_text(separator="\n", strip=True)
            else:
                text = ""
            articles = [ articles for articles in soup.find_all('article')]
            page_data = {
                'title': title,
                'url' : url,
                'content': text,
                'articles': articles
            }
            self.scraped_page.append(page_data)
            links = [link.get('href') for link in soup.find_all('a')]
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
    
    def sub_link_filter(self,links:List[str],user_prompt):
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