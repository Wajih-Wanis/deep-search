queries_prompt = """Generate {num_queries} different search queries to thoroughly research this topic: {topic}.
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