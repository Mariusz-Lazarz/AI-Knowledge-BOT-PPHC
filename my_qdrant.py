from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
load_dotenv()
import os

qdrant_url = os.getenv("QDRANT_URL")

class ClientQdrant:
    def __init__(self):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = "Piwik"

    def create_collection(self):
        try:
            collection_exists = self.client.get_collection(self.collection_name)
        except Exception as e:
            collection_exists = None

        if not collection_exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
            )
            print(f"Collection '{self.collection_name}' created successfully.")
        else:
            print(f"Collection '{self.collection_name}' already exists nothing to be performed")
    
    def upsert_points(self, points):
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point["id"],
                    payload={
                        "link": point["link"],
                        "summary": point["summary"]
                    },
                    vector=point["vector"]
                )
                for point in points
            ],
        )
        print(f"Upserted {len(points)} points into collection '{self.collection_name}'.")

    def does_point_exist(self, section_link):
        try:
            result = self.client.search(
                collection_name=self.collection_name,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="link",
                            match=models.MatchValue(value=section_link)
                        )
                    ]
                ),
                query_vector=[0.0] * 3072,
                limit=1 
            )
            return len(result) > 0 
        except Exception as e:
            print(f"Error checking existence of point: {e}")
            return False
    

    def search_points(self, vector):
        return self.client.search(collection_name=self.collection_name, 
                           query_vector=vector, limit=5, score_threshold=0.65)
