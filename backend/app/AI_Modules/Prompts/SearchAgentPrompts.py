from datetime import datetime

today = datetime.now()

todaysdate = f"Today is {today} "


queries_prompt = todaysdate+"""Generate {num_queries} different search queries to thoroughly research this topic: {topic}.
The queries generated must be google searchable.
Return your response in this exact JSON format:
{{
    "queries": ["query1", "query2", "query3"]
}}"""

relevance_prompt = """Evaluate how relevant this content is to the topic '{topic}' on a scale of 0.0 to 1.0.
Content: {content}

Return your response in this exact JSON format:
{{
    "score": 0.85,
    "reason": "Explanation of the score"
}}"""

summary_prompt = """Create a comprehensive response about {topic} using the following relevant contents.
Be sure to synthesize the information and cite sources appropriately.

Contents:
{contents}

URLs for citation:
{urls}

Return your response in this exact JSON format:
{{
    "summary": "Your detailed summary here",
    "sources": ["url1", "url2", "url3"]
}}"""

prompt_refinement_template = """
I need you to analyze and refine the following user search query to make it more effective for deep research.

Original query: "{topic}"

Please rewrite this query to:
1. Clarify the core information need
2. Identify specific aspects to explore
3. Add relevant context or constraints
4. Make it more specific and comprehensive
5. Ensure it will yield factual, authoritative sources

Return your response in the following JSON format:
{{
    "refined_query": "The refined, comprehensive search query",
    "understanding": "A brief explanation of what you understand the user is looking for",
    "search_aspects": ["list", "of", "specific", "aspects", "to", "explore"]
}}
"""

rag_prompt_template = """
Based on the following refined search query and context information, provide a comprehensive and accurate answer.

Original Query: {original_query}
Refined Understanding: {refined_query}

Context information:
{context}

Please make sure your answer:
1. Directly addresses the user's information need
2. Uses only facts from the provided context
3. Is well-structured and coherent
4. Cites the sources of information when appropriate
5. Provides deep insights that address all aspects of the query

Answer:
"""