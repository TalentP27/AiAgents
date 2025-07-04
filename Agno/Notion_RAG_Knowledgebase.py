from notion_client import Client
import os
from agno.agent import Agent
from agno.models.xai import xAI

notion = Client(auth=os.getenv("NOTION_TOKEN"))

def return_knowledge_base(agent, query, num_documents=None, **kwargs):
    database_id = "201954aae2a0809c8c1dd54f3b5037b8"
    
    try:
        results = notion.databases.query(database_id=database_id)
        
        matching_documents = []
        query_words = set(query.lower().split())
        
        for page in results['results']:
            # Extract question and answer
            question_data = page['properties']['question']['title']
            question = question_data[0]['plain_text'] if question_data else ""
            
            answer_data = page['properties']['answer']['rich_text']
            answer = answer_data[0]['plain_text'] if answer_data else ""
            
            # Better matching: check if most query words are in question or answer
            question_words = set(question.lower().split())
            answer_words = set(answer.lower().split())
            all_words = question_words.union(answer_words)
            
            # If at least 60% of query words match, it's a hit
            matches = len(query_words.intersection(all_words))
            match_ratio = matches / len(query_words) if query_words else 0
            
            if match_ratio >= 0.6:  # 60% match threshold
                # Extract metadata
                department_data = page['properties']['department']['select']
                department = department_data['name'] if department_data else "Unknown"
                
                tags_data = page['properties']['tags']['multi_select']
                tags = [tag['name'] for tag in tags_data] if tags_data else []
                
                content = f"Q: {question}\nA: {answer}"
                if tags:
                    content += f"\nTags: {', '.join(tags)}"
                
                matching_documents.append({
                    "content": content,
                    "meta_data": {
                        "source": "Company Knowledge Base",
                        "department": department,
                        "tags": tags,
                        "match_score": match_ratio
                    }
                })
        
        # Sort by match score (best matches first)
        matching_documents.sort(key=lambda x: x["meta_data"]["match_score"], reverse=True)
        
        print(f"Found {len(matching_documents)} matching documents")
        
        if matching_documents:
            return matching_documents[:num_documents] if num_documents else matching_documents
        else:
            return [{"content": "No matching entry found in the knowledge base.", "meta_data": {"source": "Company Knowledge Base"}}]
            
    except Exception as e:
        print(f"Error: {e}")
        return [{"content": f"Error: {str(e)}", "meta_data": {"source": "Error"}}]

# Set up agent
agent = Agent(
    model=xAI(id="grok-3-mini"),
    knowledge=None,
    search_knowledge=True,
    retriever=return_knowledge_base
)

# Test
prompt = input("Enter Your Prompt: ")
agent.print_response(prompt)