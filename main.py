from openai_client import OpenAIClient
from scraper import Scraper
from my_qdrant import ClientQdrant
from chat import ChatClient


def init():
    client = OpenAIClient()
    scraper = Scraper()
    qdrant = ClientQdrant()
    chat_client = ChatClient(client, scraper, qdrant, "Mario AI")

    chat_client.start()
   

if __name__ == "__main__":
    init()