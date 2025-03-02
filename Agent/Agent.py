from typing import Annotated
from typing_extensions import TypedDict, Dict, Any
import json
import operator
from langgraph.graph import END, StateGraph, START
from langgraph.constants import Send
from Utils.Model import Model
from Tools.GoogleSearch import GoogleSearchAutomator
from Tools.Scraper import Scrapy
from Types.Types import Website
import os 
import logging
from datetime import datetime
from Prompts.SearchAgentPrompts import summary_prompt,queries_prompt,relevance_prompt

if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_{current_time}.log")

class OverallState(TypedDict):
    topic: str
    search_queries: list
    search_results: Annotated[list[Website], operator.add]
    scraped_contents: Annotated[list[Website], operator.add]
    final_response: dict

class SearchState(TypedDict):
    query: str



def parse_json_response(response: str) -> Dict[str, Any]:
    try:
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON structure found")
        
        json_str = response[start_idx:end_idx]
        return json.loads(json_str)
    except Exception as e:
        logging.info(f"Agent.py: Error parsing JSON response: {str(e)}")
        return {"error": "Failed to parse response"}

class DeepSearchAgent:
    def __init__(self, model:Model):
        self.model = model
        
    def generate_search_queries(self, state: OverallState, num_queries: int = 1):
        prompt = queries_prompt.format(topic=state["topic"], num_queries=num_queries)
        response = self.model._run(prompt)
        parsed = parse_json_response(response)
        return {"search_queries": parsed.get("queries", [])}

    def execute_search(self, state: SearchState):
        search_tool = GoogleSearchAutomator()
        results = search_tool.search_google(state["query"], pages=2)
        websites = [
            Website(url=result["link"], title=result["title"], content=None) 
            for result in results
        ]
        return {"search_results": websites}

    def scrape_content(self, state: OverallState):
        scraped_sites = []
        for result in state["search_results"]:
            try:
                scraper = Scrapy(base_url=result.url, model=self.model)
                scraper.dismantle_webpage(result.url, user_prompt=state["topic"])
                if scraper.scraped_page:
                    page = scraper.scraped_page[0]
                    scraped_sites.append(
                        Website(
                            url=page['url'],
                            title=page['title'],
                            content=page['content']
                        )
                    )
            except Exception as e:
                logging.info(f"Error scraping {result.url}: {str(e)}")
                continue
        
        return {"scraped_contents": scraped_sites}

    def evaluate_relevance(self, content: str, topic: str) -> float:
        truncated_content = content[:1000] + ("..." if len(content) > 1000 else "")
        prompt = relevance_prompt.format(topic=topic, content=truncated_content)
        response = self.model._run(prompt)
        parsed = parse_json_response(response)
        return parsed.get("score", 0.0)

    def generate_final_response(self, state: OverallState):
        relevant_contents = []
        source_urls = []
        
        for item in state["scraped_contents"]:
            if not item.content:
                continue
            relevance = self.evaluate_relevance(item.content, state["topic"])
            if relevance >= 0.7:  # Threshold for relevance
                relevant_contents.append(item.content)
                source_urls.append(item.url)
        
        prompt = summary_prompt.format(
            topic=state["topic"],
            contents="\n\n".join(relevant_contents),
            urls="\n".join(source_urls)
        )
        response = self.model._run(prompt)
        parsed = parse_json_response(response)
        if not relevant_contents:
            return {"final_response": {"summary": "No relevant content found.", "sources": []}}
        return {"final_response": {
            "summary": parsed.get("summary", "No summary generated"),
            "sources": parsed.get("sources", [])
        }}

    def continue_to_search(self, state: OverallState):
        return [Send("execute_search", {"query": q}) for q in state["search_queries"]]

    def create_graph(self):
        graph = StateGraph(OverallState)
        
        graph.add_node("generate_queries", self.generate_search_queries)
        graph.add_node("execute_search", self.execute_search)
        graph.add_node("scrape_content", self.scrape_content)
        graph.add_node("generate_final", self.generate_final_response)
        
        graph.add_edge(START, "generate_queries")
        graph.add_conditional_edges(
            "generate_queries",
            self.continue_to_search,
            ["execute_search"]
        )
        graph.add_edge("execute_search", "scrape_content")
        graph.add_edge("scrape_content", "generate_final")
        graph.add_edge("generate_final", END)
        
        return graph.compile()


