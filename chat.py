import pyfiglet
import json
import logging
import os
from spinner import Spinner

## test

log_file = "chat.log"

if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(
    filename=log_file,
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG 
)

logger = logging.getLogger(__name__)

class ChatClient:
    def __init__(self, client, scraper, qdrant, banner):
        self.client = client
        self.scraper = scraper
        self.qdrant = qdrant
        self.chat_history = []
        self.banner = banner
        logger = logging.getLogger(__name__)

    def start(self):
        ascii_banner = pyfiglet.figlet_format(self.banner)
        print(ascii_banner)

        logger.info("Chat session started")

        while True:
            #get user input
            user_input = self._get_user_input()
            if user_input == "exit":
                break

            logger.debug(f"User input: {user_input}")


            self.spinner = Spinner("Generating response...")
            self.spinner.start()

            try:
                # Generate response
                context = self.generate_context(user_input)
                formatted_history = self.format_chat_history()
                # send data to a LLM for completion
                response = self.client.generate_chat_completion(
                    message=user_input, 
                    chat_history=formatted_history, 
                    context=context
                )

                logger.info(f"Generated response: {response.content}")
            finally:
                self.spinner.stop()

            print(f"AI: {response.content}")
            self.add_intercation(user_input, response.content)


    def add_intercation(self, message, response):
        """
        Adds interaction to a chat history

        Parameters: 
        message (str): Users message to add to chat history
        response (str): AI response to add to chat history

        """
        interaction = {"user": message, "assistant": response}

        self.chat_history.append(interaction)

        if len(self.chat_history) > 3:
            self.chat_history.pop(0) 

        logger.debug(f"Chat history updated: {self.chat_history}")

    def format_chat_history(self) -> str:
        """
        Formats chat history into a readable format for the AI model.

        Returns:
            str: Formatted chat history as a string.
        """
        return "\n".join(
            f"{role.upper()}: {text}" 
            for interaction in self.chat_history 
            for role, text in interaction.items()
        )
    
    def generate_context(self, user_input: str) -> str:
        """
        Generates context for the AI model based on user input.

        Parameters:
            user_input (str): The input from the user.

        Returns:
            str: A string containing the generated context.
        """
        try:
            vector = self._create_embeddings(user_input)
            search_results = self._search_relevant_points(vector)
            relevant_resources = self._fetch_and_rank_resources(search_results, user_input)
            context = self._assemble_context(relevant_resources)
        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return "Relevant Resources:\n"
        return context

    def _create_embeddings(self, user_input: str):
        """
        Generates vector embeddings from the user input.

        Parameters:
            user_input (str): The input from the user.

        Returns:
            Any: The generated vector embeddings.
        """
        return self.client.create_vector_embeddings(user_input)

    def _search_relevant_points(self, vector: list) -> list:
        """
        Searches relevant points in the Qdrant vector database.

        Parameters:
            vector: The input vector to search.

        Returns:
            list: A list of search results.
        """
        results = self.qdrant.search_points(vector)
        logger.info(f"Search results: {results}")
        return results

    def _fetch_and_rank_resources(self, search_results: list, user_input: str) -> list:
        """
        Fetches and ranks resources based on relevance.

        Parameters:
            search_results (list): Results from the Qdrant search.
            user_input (str): The input from the user.

        Returns:
            list: A list of relevant markdown resources.
        """
        relevant_resources = []

        for result in search_results:
            link = result.payload.get("link")
            if not link:
                continue

            try:
                section_content = self.scraper.scrape_section_content(link)
                section_md = self.scraper.create_section_markdown(section_content)
                relevance = self.client.re_rank_resources(section_md, user_input)
                is_relevant = self._parse_relevance(relevance)

                if is_relevant:
                    relevant_resources.append(section_md)
            except Exception as e:
                logger.error(f"Error processing resource {link}: {e}")

        return relevant_resources

    def _parse_relevance(self, relevance: str) -> bool:
        """
        Parses the relevance response from the AI re-ranker.

        Parameters:
            relevance (str): The JSON response string from the re-ranker.

        Returns:
            bool: Whether the resource is relevant.
        """
        try:
            relevance_data = json.loads(relevance)
            return relevance_data.get("relevance") == 1
        except json.JSONDecodeError:
            logger.warning(f"Invalid relevance response: {relevance}")
            return False

    def _assemble_context(self, relevant_resources: list) -> str:
        """
        Assembles relevant resources into a single context string.

        Parameters:
            relevant_resources (list): List of relevant markdown resources.

        Returns:
            str: The assembled context string.
        """
        context = "Relevant Resources:\n"
        for resource in relevant_resources:
            context += f"Content:\n{resource}\n"
        logger.info(f"Generated context: {context}")
        return context

    @staticmethod
    def _get_user_input() -> str:
        while True:
            user_input = input("User Input: ").strip()
            if user_input:
                return user_input
            print("Input cannot be empty. Please try again.")

    

