from openai import OpenAI
from dotenv import load_dotenv
import prompts
import os

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=openai_key)

    def generate_chat_completion(self, message, chat_history, context):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompts.main_prompt(chat_history, context)},
                {"role": "user", "content": message}
            ]
        )
        return completion.choices[0].message

    def summarize_article(self, article_content):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompts.summary_prompt},
                {"role": "user", "content": article_content}
            ]
        )
        return completion.choices[0].message.content
    
    def create_vector_embeddings(self, content):
        response = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=content
        )

        return response.data[0].embedding
    
    def re_rank_resources(self, resource, user_query):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
             messages=[
                {"role": "system", "content": prompts.rerank_prompt},
                {"role": "user", "content": f"User Question: {user_query}, Resource: {resource}"}
            ],
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "relevance_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "relevance": {
                                "description": "Relevance of the resource to the user's query",
                                "type": "integer",
                                "enum": [0, 1]
                            }
                        },
                        "required": ["relevance"],
                        "additionalProperties": False
                    }
                }
            }
            
        )

        return completion.choices[0].message.content