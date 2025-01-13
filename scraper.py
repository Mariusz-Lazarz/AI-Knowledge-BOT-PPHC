import requests
from bs4 import BeautifulSoup
import re
import html2text

class Scraper():
    def __init__(self):
        self.base_helpcenter_url = "https://help.piwik.pro/"
        self.exclude_links =  {
            "https://help.piwik.pro/support/video-tutorials/",
            "https://help.piwik.pro/support/developers-api/",
            "https://help.piwik.pro/support/audiences/"
        }
        
    def fetch_html(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}. Error: {e}")
            return None
        
    @staticmethod
    def extract_links_from_html(html, tag, class_name=None):
        soup = BeautifulSoup(html, 'html.parser')
        if class_name:
            elements = soup.find_all(tag, class_=class_name)
        else:
            elements = soup.find_all(tag)

        links = []
        for element in elements:
            links.extend(a.get('href') for a in element.find_all('a'))
        return links
    
    def get_main_links(self):
        html = self.fetch_html(self.base_helpcenter_url)
        if not html:
            return []

        links = self.extract_links_from_html(html, 'h3')
        return [link for link in links if link not in self.exclude_links]
    
    
    def get_article_links(self):
        main_links = self.get_main_links()
        article_links = []

        for article_link in main_links:
            html = self.fetch_html(article_link)
            if not html:
                continue
            
            content_links = self.extract_links_from_html(html, 'div', 'content mt-8') + \
                            self.extract_links_from_html(html, 'ol', 'darklist')
            
            article_links.extend(content_links)
        
        return article_links
    
    def get_all_links(self):
        article_links = self.get_article_links()

        all_article_links = set()
        for link in article_links:
            section_links = self.scrape_sections_links(link)
            all_article_links.update(section_links)

        return all_article_links
    

    def scrape_sections_links(self, link):
        html = self.fetch_html(link)
        soup = BeautifulSoup(html, "html.parser")

        article = soup.select_one("article")
        if not article:
            print(f"No article section found for {link}")
            return [link]

        anchors = article.find_all("a", class_="heading-anchor")

        if not anchors:
            return [link]

        links = []
        for anchor in anchors:
            anchor_href = anchor.get("href")
            if anchor_href:
                if anchor_href.startswith("#"):
                    full_url = f"{link.rstrip('/')}{anchor_href}"
                    links.append(full_url)
                else:
                    links.append(anchor_href)

        return links
    
    def scrape_section_content(self, link):
        html = self.fetch_html(link)
        soup = BeautifulSoup(html, "html.parser")

        article = soup.select_one("article")
        if not article:
            print(f"No article section found for link: {link}")
            return None

        section_id_match = re.search(r'#(.*)', link)
        if section_id_match:
            section_id = section_id_match.group(1)
            
            target_heading = soup.find(lambda tag: tag.name in ['h2', 'h3'] and tag.get('id') == section_id)
            if target_heading:
                content = []
                for sibling in target_heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:
                        break
                    content.append(str(sibling))
                # Prepend the link to the content
                content.insert(0, f'<p>Source: \n <a href="{link}">{link}</a></p>')
                return ''.join(content)
            else:
                # Prepend the link to the full article text
                return f'<p>Source: \n <a href="{link}">{link}</a></p>{article.get_text(strip=True)}'
        else:
            # Prepend the link to the full article text
            return f'<p>Source: \n <a href="{link}">{link}</a></p>{article.get_text(strip=True)}'

        
    @staticmethod
    def create_section_markdown(content):
        if not content:
            raise ValueError("Content cannot be None or empty.")

        is_html_like = '<' in content and '>' in content

        if is_html_like:
            markdown_converter = html2text.HTML2Text()
            markdown_converter.ignore_links = False

            markdown_content = markdown_converter.handle(content)
        else:
            markdown_content = content

        return markdown_content.strip() + "\n"