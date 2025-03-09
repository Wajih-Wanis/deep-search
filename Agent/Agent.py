from typing import Annotated, Literal, Optional, List
from typing_extensions import TypedDict, Dict, Any
import json
import operator
from langgraph.graph import END, StateGraph, START
from langgraph.constants import Send
from Utils.Model import Model
from Tools.GoogleSearch import GoogleSearchAutomator
from Tools.Scraper import Scrapy
from Types.Types import Website
from Utils.Retriever import FaissRetriever, GraphRetriever
from langchain_core.documents import Document
import os 
import logging
from datetime import datetime
from Prompts.SearchAgentPrompts import summary_prompt, queries_prompt, prompt_refinement_template,rag_prompt_template

if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"log_{current_time}.log")

logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s - %(funcName)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class OverallState(TypedDict):
    topic: str
    refined_topic: dict
    search_queries: list
    search_results: Annotated[list[Website], operator.add]
    scraped_contents: Annotated[list[Website], operator.add]
    final_response: dict
    retriever_type: str  
    vector_retriever: Any  
    graph_retriever: Any 
    rag_response: dict   

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
        logging.error(f"Agent Log: Error parsing JSON response: {str(e)}")
        logging.debug(f"Agent Log: Original response: {response[:200]}...")
        return {"error": "Failed to parse response"}

class DeepSearchAgent:
    def __init__(self, model: Model, retriever_type: str = "vector"):
        self.model = model
        self.retriever_type = retriever_type
        logging.info(f"Agent Log: Initializing DeepSearchAgent with retriever type: {retriever_type}")
    
    def refine_user_prompt(self, state: OverallState):
        """Analyze and refine the user's original query to better understand their intent"""
        logging.info(f"Agent Log: Refining user prompt: {state['topic']}")
        prompt = prompt_refinement_template.format(topic=state["topic"])
        logging.debug(f"Agent Log: Prompt refinement template: {prompt[:200]}...")
        
        response = self.model._run(prompt)
        logging.debug(f"Agent Log: Model response for prompt refinement: {response[:200]}...")
        
        parsed = parse_json_response(response)
        refined_topic = {
            "refined_query": parsed.get("refined_query", state["topic"]),
            "understanding": parsed.get("understanding", "No understanding generated"),
            "search_aspects": parsed.get("search_aspects", [])
        }
        
        logging.info(f"Agent Log: Original query: '{state['topic']}' refined to: '{refined_topic['refined_query']}'")
        logging.info(f"Agent Log: Identified {len(refined_topic['search_aspects'])} search aspects")
        
        return {
            "refined_topic": refined_topic
        }
        
    def generate_search_queries(self, state: OverallState, num_queries: int = 3):
        logging.info(f"Agent Log: Generating search queries based on refined topic")
        
        original_topic = state["topic"]
        refined_query = state["refined_topic"]["refined_query"]
        search_aspects = state["refined_topic"]["search_aspects"]
        
        if search_aspects:
            combined_topic = f"Main query: {refined_query}\nAspects to explore: {', '.join(search_aspects)}"
        else:
            combined_topic = refined_query
            
        prompt = queries_prompt.format(topic=combined_topic, num_queries=num_queries)
        logging.debug(f"Agent Log: Query generation prompt: {prompt[:200]}...")
        
        response = self.model._run(prompt)
        logging.debug(f"Agent Log: Model response for query generation: {response[:200]}...")
        
        parsed = parse_json_response(response)
        queries = parsed.get("queries", [])
        
        if not queries:
            logging.warning("Agent Log: No queries generated, using refined query as fallback")
            queries = [refined_query]
            
            if search_aspects:
                for aspect in search_aspects[:2]:  
                    combined_query = f"{refined_query} {aspect}"
                    if combined_query not in queries:
                        queries.append(combined_query)
        
        logging.info(f"Agent Log: Generated {len(queries)} search queries: {queries}")
        
        return {
            "search_queries": queries,
            "retriever_type": self.retriever_type
        }

    def execute_search(self, state: SearchState):
        logging.info(f"Agent Log: Executing search for query: {state['query']}")
        search_tool = GoogleSearchAutomator()
        
        try:
            results = search_tool.search_google(state["query"], pages=1)
            logging.info(f"Agent Log: Found {len(results)} search results")
            logging.debug(f"Agent Log: Search results: {results[:3]}")
            
            websites = [
                Website(url=result["link"], title=result["title"], content=None) 
                for result in results
            ]
            logging.info(f"Agent Log: Processed {len(websites)} website entries")
            return {"search_results": websites}
            
        except Exception as e:
            logging.error(f"Agent Log: Error during search execution: {str(e)}")
            return {"search_results": []}

    def scrape_content(self, state: OverallState):
        logging.info(f"Agent Log: Starting content scraping for {len(state['search_results'])} websites")
        scraped_sites = []
        
        for i, result in enumerate(state["search_results"]):
            try:
                logging.info(f"Agent Log: Scraping content from [{i+1}/{len(state['search_results'])}]: {result.url}")
                scraper = Scrapy(base_url=result.url, model=self.model)
                
                refined_query = state["refined_topic"]["refined_query"]
                scraper.dismantle_webpage(result.url, user_prompt=refined_query)
                
                if scraper.scraped_page:
                    page = scraper.scraped_page[0]
                    scraped_sites.append(
                        Website(
                            url=page['url'],
                            title=page['title'],
                            content=page['content']
                        )
                    )
                    logging.info(f"Agent Log: Successfully scraped content from {result.url} ({len(page['content'])} chars)")
                    logging.debug(f"Agent Log: Content sample: {page['content'][:200]}...")
                else:
                    logging.warning(f"Agent Log: No content scraped from {result.url}")
            except Exception as e:
                logging.error(f"Agent Log: Error scraping {result.url}: {str(e)}")
                continue
        
        logging.info(f"Agent Log: Completed scraping with {len(scraped_sites)} successful results")
        return {"scraped_contents": scraped_sites}

    def build_knowledge_bases(self, state: OverallState):
        """Build the vector store and/or knowledge graph based on scraped content"""
        logging.info("Agent Log: Agent Log: Starting to build knowledge bases")
        from langchain_ollama import OllamaEmbeddings
        
        try:
            embedding_model = OllamaEmbeddings(model="llama3.2:1b")
            logging.info("Agent Log: Successfully initialized embedding model")
        except Exception as e:
            logging.error(f"Agent Log: Failed to initialize embedding model: {str(e)}")
            return {
                "vector_retriever": None,
                "graph_retriever": None
            }
        
        documents = []
        metadatas = []
        
        for site in state["scraped_contents"]:
            if site.content:
                documents.append(site.content)
                metadatas.append({"source": site.url, "title": site.title})
        
        logging.info(f"Agent Log: Extracted {len(documents)} documents from scraped content")
        
        if not documents:
            logging.warning("Agent Log: No documents to build knowledge bases from")
            return {
                "vector_retriever": None,
                "graph_retriever": None
            }
        
        vector_retriever = None
        graph_retriever = None
        retriever_type = state["retriever_type"]
        
        if retriever_type in ["vector", "both"]:
            try:
                logging.info("Agent Log: Building vector retriever")
                vector_retriever = FaissRetriever(
                    embedding_model=embedding_model,
                    index_name="user_query_index",
                    persist_directory="./vector_stores"
                )
                vector_retriever.ingest(documents, metadatas)
                
                if not hasattr(vector_retriever, 'vector_store') or vector_retriever.vector_store is None:
                    logging.error("Agent Log: Vector store was not properly initialized")
                    vector_retriever = None
                else:
                    logging.info("Agent Log: Vector retriever built successfully")
            except Exception as e:
                logging.error(f"Agent Log: Error building vector retriever: {str(e)}")
                vector_retriever = None
        
        if retriever_type in ["graph", "both"]:
            try:
                logging.info("Agent Log: Building graph retriever")
                graph_retriever = GraphRetriever(
                    embedding_model=embedding_model,
                    similarity_threshold=0.7
                )
                graph_retriever.ingest(documents, metadatas)
                logging.info("Agent Log: Graph retriever built successfully")
            except Exception as e:
                logging.error(f"Agent Log: Error building graph retriever: {str(e)}")
                graph_retriever = None
        
        return {
            "vector_retriever": vector_retriever,
            "graph_retriever": graph_retriever
        }

    def perform_rag_query(self, state: OverallState):
        """Perform RAG query using the built retrievers and refined understanding"""
        original_topic = state["topic"]
        refined_topic = state["refined_topic"]["refined_query"]
        understanding = state["refined_topic"]["understanding"]
        retriever_type = state["retriever_type"]
        vector_retriever = state["vector_retriever"] 
        graph_retriever = state["graph_retriever"]
        
        logging.info(f"Agent Log: Performing RAG query with refined understanding")
        logging.info(f"Agent Log: Original topic: {original_topic}")
        logging.info(f"Agent Log: Refined topic: {refined_topic}")
        logging.info(f"Agent Log: Using retriever type: {retriever_type}")
        
        if not (vector_retriever or graph_retriever):
            logging.warning("Agent Log: No retrievers available for RAG query")
            return {"rag_response": {
                "answer": "Unable to perform RAG query as no retrievers were successfully built.",
                "sources": []
            }}
        
        retrieved_docs = []
        sources = []
        
        query_string = refined_topic
        
        if retriever_type == "vector" and vector_retriever:
            try:
                logging.info(f"Agent Log: Querying vector retriever with: {query_string}")
                retrieved_docs = vector_retriever.query(query_string, k=5)
                logging.info(f"Agent Log: Retrieved {len(retrieved_docs)} documents from vector retriever")
            except ValueError as ve:
                logging.error(f"Agent Log: Vector retriever error: {str(ve)}")
                logging.warning("Agent Log: Vector store not initialized. Setting retrieved_docs to empty list.")
                retrieved_docs = []
            except Exception as e:
                logging.error(f"Agent Log: Error querying vector retriever: {str(e)}")
                retrieved_docs = []
                
        elif retriever_type == "graph" and graph_retriever:
            try:
                logging.info(f"Agent Log: Querying graph retriever with: {query_string}")
                retrieved_docs = graph_retriever.query(query_string, k=5)
                logging.info(f"Agent Log: Retrieved {len(retrieved_docs)} documents from graph retriever")
            except Exception as e:
                logging.error(f"Agent Log: Error querying graph retriever: {str(e)}")
                retrieved_docs = []
                
        elif retriever_type == "both":
            vector_docs = []
            graph_docs = []
            
            if vector_retriever:
                try:
                    logging.info(f"Agent Log: Querying vector retriever in 'both' mode with: {query_string}")
                    vector_docs = vector_retriever.query(query_string, k=3)
                    logging.info(f"Agent Log: Retrieved {len(vector_docs)} documents from vector retriever")
                except ValueError as ve:
                    logging.error(f"Agent Log: Vector retriever error: {str(ve)}")
                except Exception as e:
                    logging.error(f"Agent Log: Error querying vector retriever: {str(e)}")
                    
            if graph_retriever:
                try:
                    logging.info(f"Agent Log: Querying graph retriever in 'both' mode with: {query_string}")
                    graph_docs = graph_retriever.query(query_string, k=3)
                    logging.info(f"Agent Log: Retrieved {len(graph_docs)} documents from graph retriever")
                except Exception as e:
                    logging.error(f"Agent Log: Error querying graph retriever: {str(e)}")
            
            doc_urls = set()
            for doc in vector_docs + graph_docs:
                url = doc.metadata.get("source", "")
                if url not in doc_urls:
                    retrieved_docs.append(doc)
                    doc_urls.add(url)
            
            retrieved_docs = retrieved_docs[:5]
            logging.info(f"Agent Log: Combined {len(retrieved_docs)} unique documents from both retrievers")
        
        context = ""
        for i, doc in enumerate(retrieved_docs):
            content = doc.page_content
            source = doc.metadata.get("source", "Unknown source")
            context += f"Source: {source}\n{content}\n\n"
            sources.append(source)
            logging.debug(f"Agent Log: Document {i+1}: Source={source}, Content length={len(content)}")
        
        if context:
            rag_prompt = rag_prompt_template.format(
                original_query=original_topic,
                refined_query=understanding or refined_topic,
                context=context
            )
            logging.info(f"Agent Log: Generating RAG response with {len(context)} chars of context")
            logging.debug(f"Agent Log: RAG prompt: {rag_prompt[:200]}...")
            
            response = self.model._run(rag_prompt)
            logging.debug(f"Agent Log: RAG response: {response[:200]}...")
            
            return {"rag_response": {
                "answer": response,
                "sources": list(set(sources))   
            }}
        else:
            logging.warning("Agent Log: No context was extracted from retrieved documents")
            return {"rag_response": {
                "answer": "No relevant information found in the knowledge base.",
                "sources": []
            }}

    def generate_final_response(self, state: OverallState):
        logging.info("Agent Log: Generating final response")
        relevant_contents = []
        source_urls = []
        
        for item in state["scraped_contents"]:
            if not item.content:
                continue
            logging.debug(f"Agent Log: Including content from {item.url} ({len(item.content)} chars)")
            relevant_contents.append(item.content)
            source_urls.append(item.url)
        
        if relevant_contents:
            logging.info(f"Agent Log: Generating summary from {len(relevant_contents)} content pieces")
            
            original_topic = state["topic"]
            refined_topic = state["refined_topic"]["refined_query"]
            understanding = state["refined_topic"]["understanding"]
            
            enriched_topic = f"""
Original query: {original_topic}
Refined understanding: {understanding}
Refined query: {refined_topic}
            """
            
            prompt = summary_prompt.format(
                topic=enriched_topic,
                contents="\n\n".join(relevant_contents),
                urls="\n".join(source_urls)
            )
            logging.debug(f"Agent Log: Summary prompt: {prompt[:200]}...")
            
            summary_response = self.model._run(prompt)
            logging.debug(f"Agent Log: Summary response: {summary_response[:200]}...")
            
            parsed_summary = parse_json_response(summary_response)
            final_summary = parsed_summary.get("summary", "No summary generated")
            final_sources = parsed_summary.get("sources", [])
        else:
            logging.warning("Agent Log: No relevant content found for summary generation")
            final_summary = "No relevant content found from traditional search."
            final_sources = []
        
        rag_answer = state["rag_response"].get("answer", "No RAG answer generated")
        rag_sources = state["rag_response"].get("sources", [])
        
        all_sources = list(set(final_sources + rag_sources))
        
        refined_topic = state["refined_topic"]
        
        logging.info(f"Agent Log: Final response generated with {len(all_sources)} sources")
        return {"final_response": {
            "original_query": state["topic"],
            "refined_understanding": refined_topic.get("understanding", ""),
            "search_aspects": refined_topic.get("search_aspects", []),
            "search_summary": final_summary,
            "rag_answer": rag_answer,
            "sources": all_sources
        }}

    def continue_to_search(self, state: OverallState):
        queries = state["search_queries"]
        logging.info(f"Agent Log: Continuing to search with {len(queries)} queries")
        return [Send("execute_search", {"query": q}) for q in queries]

    def create_graph(self):
        logging.info("Agent Log: Creating state graph for the agent workflow")
        graph = StateGraph(OverallState)
        
        graph.add_node("refine_prompt", self.refine_user_prompt)
        graph.add_node("generate_queries", self.generate_search_queries)
        graph.add_node("execute_search", self.execute_search)
        graph.add_node("scrape_content", self.scrape_content)
        graph.add_node("build_knowledge_bases", self.build_knowledge_bases)
        graph.add_node("perform_rag_query", self.perform_rag_query)
        graph.add_node("generate_final", self.generate_final_response)
        
        graph.add_edge(START, "refine_prompt")
        graph.add_edge("refine_prompt", "generate_queries")
        graph.add_conditional_edges(
            "generate_queries",
            self.continue_to_search,
            ["execute_search"]
        )
        graph.add_edge("execute_search", "scrape_content")
        graph.add_edge("scrape_content", "build_knowledge_bases")
        graph.add_edge("build_knowledge_bases", "perform_rag_query")
        graph.add_edge("perform_rag_query", "generate_final")
        graph.add_edge("generate_final", END)
        
        logging.info("Agent Log: State graph created and compiled")
        return graph.compile()