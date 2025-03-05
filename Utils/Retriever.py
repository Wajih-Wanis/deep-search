from abc import abstractmethod, ABC
from typing import List, Dict, Any, Optional, Union
import os
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
import networkx as nx
import re
import matplotlib.pyplot as plt
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline, AutoModel
import logging
from datetime import datetime


if not os.path.exists('logs'):
    os.makedirs('logs')

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join('logs', f"retriever_log_{current_time}.log")


logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Retriever(ABC):
  
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def ingest(self, documents: List[Union[str, Document]], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        pass 
    
    @abstractmethod
    def query(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        pass
    
    @abstractmethod
    def rerank(self, query: str, documents: List[Document], top_k: int = 3) -> List[Document]:
        pass


class FaissRetriever(Retriever):
    
    def __init__(self, 
                 embedding_model: Embeddings,
                 index_name: str = "faiss_index",
                 persist_directory: Optional[str] = None):
        self.embedding_model = embedding_model
        self.index_name = index_name
        self.persist_directory = persist_directory
        self.vector_store = None
        self.reranker = None
    
    def ingest(self, 
               documents: List[Union[str, Document]], 
               metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        if documents and isinstance(documents[0], str):
            if metadatas:
                docs = [Document(page_content=doc, metadata=meta) 
                        for doc, meta in zip(documents, metadatas)]
            else:
                docs = [Document(page_content=doc) for doc in documents]
        else:
            docs = documents
            
        
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(
                documents=docs,
                embedding=self.embedding_model,
                index_name=self.index_name
            )
        else:
            self.vector_store.add_documents(documents=docs)
        
        
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vector_store.save_local(self.persist_directory)
    
    def query(self, 
              query: str, 
              k: int = 5, 
              filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        if self.vector_store is None:
            raise ValueError("Vector store has not been initialized. Please ingest documents first.")
        
        results = self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
        
        return results
    
    def rerank(self, 
               query: str, 
               documents: List[Document], 
               top_k: int = 3) -> List[Document]:
        if self.reranker is None:
            
            
            
            query_embedding = self.embedding_model.embed_query(query)
            
            
            document_scores = []
            for doc in documents:
                doc_embedding = self.embedding_model.embed_documents([doc.page_content])[0]
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                document_scores.append((doc, similarity))
                
            
            document_scores.sort(key=lambda x: x[1], reverse=True)
            
            
            return [doc for doc, _ in document_scores[:top_k]]
        else:
            
            return self.reranker.rerank(query, documents, top_k)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def load(self, path: Optional[str] = None) -> None:
        load_path = path or self.persist_directory
        if not load_path:
            raise ValueError("No path specified and no persist_directory set during initialization")
        
        self.vector_store = FAISS.load_local(
            folder_path=load_path,
            embeddings=self.embedding_model,
            index_name=self.index_name
        )
    
    def set_reranker(self, reranker: Any) -> None:
        self.reranker = reranker



class GraphRetriever(Retriever):
    
    def __init__(
        self, 
        embedding_model: Embeddings,
        ner_model_name: str = "dslim/bert-base-NER", 
        min_entity_length: int = 2,
        similarity_threshold: float = 0.75,
        window_size: int = 5
    ):
        self.G = nx.Graph()
        self.min_entity_length = min_entity_length
        self.similarity_threshold = similarity_threshold
        self.window_size = window_size
        self.embedding_model = embedding_model
        self.reranker = None
        
        
        try:
            self.ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_name)
            self.ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_name)
            self.ner_pipeline = pipeline(
                "ner", 
                model=self.ner_model, 
                tokenizer=self.ner_tokenizer,
                aggregation_strategy="simple"
            )
            self.use_hf_ner = True
        except Exception as e:
            logging.info(f"Error loading NER model: {e}")
            self.use_hf_ner = False
                
        
        self.node_sources = {}
        
        self.edge_weights = {}
        
        self.entity_embeddings = {}
        
        self.entity_chunks = defaultdict(list)
    
    def _extract_entities_regex(self, text: str) -> List[str]:
        entities = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', text)
        
        stop_words = {"I", "The", "A", "An", "This", "That", "These", "Those"}
        return [e for e in entities if e not in stop_words and len(e) >= self.min_entity_length]
    
    def _extract_entities_hf(self, text: str) -> List[str]:
        ner_results = self.ner_pipeline(text)
        
        
        entities = []
        for entity in ner_results:
            entity_text = entity["word"]
            if len(entity_text) >= self.min_entity_length:
                entities.append(entity_text)
                
        return entities
    
    def extract_entities(self, text: str) -> List[str]:
        if self.use_hf_ner:
            return self._extract_entities_hf(text)
        else:
            return self._extract_entities_regex(text)
    
    def compute_embedding(self, text: str) -> np.ndarray:
        embedding = self.embedding_model.embed_query(text)
        
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)
            
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    def are_similar_entities(self, entity1: str, entity2: str) -> bool: 
        if entity1 not in self.entity_embeddings:
            self.entity_embeddings[entity1] = self.compute_embedding(entity1)
        if entity2 not in self.entity_embeddings:
            self.entity_embeddings[entity2] = self.compute_embedding(entity2)
            
        similarity = np.dot(self.entity_embeddings[entity1], self.entity_embeddings[entity2])
        
        return similarity > self.similarity_threshold
    
    def get_canonical_entity(self, entity: str) -> str:
        
        for existing_entity in self.G.nodes():
            if self.are_similar_entities(entity, existing_entity):
                return existing_entity
                
        
        return entity
    
    def extract_relationships(self, text: str) -> List[tuple]:
        entities = self.extract_entities(text)
        relationships = []
        
        
        if len(entities) < 2:
            return relationships
        
        
        for i in range(len(entities)):
            
            canonical_i = self.get_canonical_entity(entities[i])
            
            for j in range(i + 1, min(i + self.window_size, len(entities))):
                
                canonical_j = self.get_canonical_entity(entities[j])
                
                
                if canonical_i == canonical_j:
                    continue
                    
                
                weight = 1.0 / (j - i)
                relationships.append((canonical_i, canonical_j, weight))
                
        return relationships
    
    def ingest(self, 
              documents: List[Union[str, Document]], 
              metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        
        if documents and isinstance(documents[0], str):
            if metadatas:
                docs = [Document(page_content=doc, metadata=meta) 
                        for doc, meta in zip(documents, metadatas)]
            else:
                docs = [Document(page_content=doc) for doc in documents]
        else:
            docs = documents
            
        
        for i, doc in enumerate(docs):
            
            relationships = self.extract_relationships(doc.page_content)
            
            
            source_info = doc.metadata.get("source", "unknown")
            
            
            for entity1, entity2, weight in relationships:
                
                if entity1 not in self.G:
                    self.G.add_node(entity1)
                    self.node_sources[entity1] = set()
                if entity2 not in self.G:
                    self.G.add_node(entity2)
                    self.node_sources[entity2] = set()
                    
                
                self.node_sources[entity1].add(source_info)
                self.node_sources[entity2].add(source_info)
                
                
                self.entity_chunks[entity1].append(doc)
                self.entity_chunks[entity2].append(doc)
                
                
                if self.G.has_edge(entity1, entity2):
                    
                    edge_key = tuple(sorted([entity1, entity2]))
                    self.edge_weights[edge_key] = self.edge_weights.get(edge_key, 1.0) + weight
                else:
                    
                    self.G.add_edge(entity1, entity2)
                    edge_key = tuple(sorted([entity1, entity2]))
                    self.edge_weights[edge_key] = weight
            
            if (i + 1) % 10 == 0:
                logging.info(f"Processed {i+1}/{len(docs)} documents")
                
        
        for edge in self.G.edges():
            sorted_edge = tuple(sorted(edge))
            nx.set_edge_attributes(self.G, {edge: {"weight": self.edge_weights.get(sorted_edge, 1.0)}})
            
        logging.info(f"Knowledge graph built with {len(self.G.nodes())} entities and {len(self.G.edges())} relationships")
    
    def query(self, 
             query: str, 
             k: int = 5, 
             filter: Optional[Dict[str, Any]] = None) -> List[Document]:

        query_entities = self.extract_entities(query)
        
        
        if not query_entities:
            query_terms = [word.lower() for word in re.findall(r'\b\w+\b', query) 
                          if len(word) > 2]
            
            matched_nodes = []
            for node in self.G.nodes:
                node_lower = node.lower()
                if any(term in node_lower for term in query_terms):
                    matched_nodes.append(node)
        else:
            
            matched_nodes = []
            for entity in query_entities:
                canonical = self.get_canonical_entity(entity)
                if canonical in self.G:
                    matched_nodes.append(canonical)
        
        if not matched_nodes:
            return []
            
        
        query_embedding = self.compute_embedding(query)
        
        
        node_scores = {}
        for node in matched_nodes:
            if node not in self.entity_embeddings:
                self.entity_embeddings[node] = self.compute_embedding(node)
            similarity = np.dot(query_embedding, self.entity_embeddings[node])
            node_scores[node] = similarity
            
        
        matched_nodes = sorted(matched_nodes, key=lambda n: node_scores.get(n, 0), reverse=True)
        
        
        related_nodes = set()
        for node in matched_nodes[:min(k, len(matched_nodes))]:
            related_nodes.update(self.G.neighbors(node))
            
        
        context_docs = set()
        for node in list(matched_nodes) + list(related_nodes):
            for doc in self.entity_chunks.get(node, []):
                context_docs.add(doc)
                
        
        doc_scores = {}
        entities_of_interest = set(matched_nodes).union(related_nodes)
        for doc in context_docs:
            score = 0
            doc_entities = self.extract_entities(doc.page_content)
            doc_entities = [self.get_canonical_entity(e) for e in doc_entities]
            
            for entity in doc_entities:
                if entity in entities_of_interest:
                    score += node_scores.get(entity, 0.5)
                    
            
            doc_embedding = self.compute_embedding(doc.page_content)
            query_similarity = np.dot(query_embedding, doc_embedding)
            
            
            doc_scores[doc] = score + query_similarity
            
        
        result_docs = sorted(list(context_docs), key=lambda d: doc_scores.get(d, 0), reverse=True)
        return result_docs[:k]
    
    def rerank(self, 
              query: str, 
              documents: List[Document], 
              top_k: int = 3) -> List[Document]:
        
        if self.reranker is None:
            
            query_entities = self.extract_entities(query)
            query_embedding = self.compute_embedding(query)
            
            
            document_scores = []
            for doc in documents:
                
                score = 0
                doc_entities = self.extract_entities(doc.page_content)
                
                
                for query_entity in query_entities:
                    canonical_query = self.get_canonical_entity(query_entity)
                    for doc_entity in doc_entities:
                        canonical_doc = self.get_canonical_entity(doc_entity)
                        if canonical_query == canonical_doc:
                            score += 1
                            
                
                doc_embedding = self.compute_embedding(doc.page_content)
                similarity = np.dot(query_embedding, doc_embedding)
                
                
                final_score = score + similarity
                document_scores.append((doc, final_score))
                
            
            document_scores.sort(key=lambda x: x[1], reverse=True)
            
            
            return [doc for doc, _ in document_scores[:top_k]]
        else:
            
            return self.reranker.rerank(query, documents, top_k)
    
    def set_reranker(self, reranker: Any) -> None:
       
        self.reranker = reranker
            
    def visualize_graph(self, query: Optional[str] = None, 
                       max_nodes: int = 30, save_path: Optional[str] = None) -> None:
       
        if len(self.G) == 0:
            logging.info("Graph is empty - nothing to visualize")
            return
            
        
        if len(self.G) > max_nodes:
            if query:
                
                query_entities = self.extract_entities(query)
                matched_nodes = []
                for entity in query_entities:
                    canonical = self.get_canonical_entity(entity)
                    if canonical in self.G:
                        matched_nodes.append(canonical)
                        
                
                nodes_to_show = set(matched_nodes)
                for node in matched_nodes:
                    nodes_to_show.update(self.G.neighbors(node))
                    
                
                if len(nodes_to_show) < max_nodes:
                    degree_dict = dict(self.G.degree())
                    high_degree_nodes = sorted(degree_dict, key=degree_dict.get, reverse=True)
                    nodes_to_show.update(high_degree_nodes[:max_nodes-len(nodes_to_show)])
            else:
                
                degree_dict = dict(self.G.degree())
                nodes_to_show = sorted(degree_dict, key=degree_dict.get, reverse=True)[:max_nodes]
                
            viz_graph = self.G.subgraph(list(nodes_to_show)[:max_nodes])
        else:
            viz_graph = self.G
            
        
        pos = nx.spring_layout(viz_graph, seed=42)
        
        
        plt.figure(figsize=(10, 8))
        
        
        node_colors = []
        node_sizes = []
        
        if query:
            query_entities = self.extract_entities(query)
            matched_nodes = []
            for entity in query_entities:
                canonical = self.get_canonical_entity(entity)
                if canonical in self.G:
                    matched_nodes.append(canonical)
                    
            for node in viz_graph.nodes():
                if node in matched_nodes:
                    node_colors.append('red')
                    node_sizes.append(300)
                elif any(nx.has_path(viz_graph, node, m) for m in matched_nodes):
                    node_colors.append('orange')
                    node_sizes.append(200)
                else:
                    node_colors.append('skyblue')
                    node_sizes.append(100)
        else:
            node_colors = ['skyblue'] * len(viz_graph)
            node_sizes = [100] * len(viz_graph)
            
        
        nx.draw_networkx_nodes(viz_graph, pos, node_color=node_colors, 
                              node_size=node_sizes, alpha=0.8)
        
        
        for u, v, attrs in viz_graph.edges(data=True):
            edge_key = tuple(sorted([u, v]))
            width = 1 + (self.edge_weights.get(edge_key, 1.0) / 2)
            nx.draw_networkx_edges(viz_graph, pos, edgelist=[(u, v)], 
                                 width=width, alpha=0.5)
        
        
        nx.draw_networkx_labels(viz_graph, pos, font_size=8)
        
        
        plt.axis('off')
        
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            logging.info(f"Graph visualization saved to {save_path}")
        
        
        plt.show()