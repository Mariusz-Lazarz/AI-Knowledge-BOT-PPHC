from openai_client import OpenAIClient
from my_qdrant import ClientQdrant
from scraper import Scraper
import uuid
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__) 


def create_point(link, summary, vector):
    return {
        "id": str(uuid.uuid4()),
        "link": link,
        "summary": summary,
        "vector": vector
    }

def init():
    logger.info("Initializing scraper...")
    client = OpenAIClient()
    qdrant = ClientQdrant()
    scraper = Scraper()
    qdrant.create_collection()
    logger.info("Qdrant collection created.")

    all_article_links = scraper.get_article_links()

    for link in all_article_links:
        logger.info(f"Processing link: {link}")
        points = []

        try:
            content = scraper.scrape_section_content(link)
            section_md = scraper.create_section_markdown(content)

            if qdrant.does_point_exist(link):
                logger.warning(f"Skipping existing entry: {link}")
                continue

            summary = client.summarize_article(section_md)
            logger.debug(f"Summary for {link}: {summary}")

            vector = client.create_vector_embeddings(summary)
            logger.debug(f"Vector embeddings for {link}")

            point = create_point(link, summary, vector)
            logger.info(f"Created point for {link}")

            points.append(point)
            qdrant.upsert_points(points)

            logger.info(f"Successfully processed {link}")
        except Exception as e:
            logger.error(f"Error processing link {link}: {e}", exc_info=True)

    logger.info("Scraping completed.")

init()