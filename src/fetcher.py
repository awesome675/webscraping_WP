import requests
import os
from os.path import join, dirname
from bs4 import BeautifulSoup
import json
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts, EditPost
from dotenv import load_dotenv


load_dotenv()

WP_USERNAME = os.environ.get("WP_USERNAME")
WP_PASSWORD = os.environ.get("WP_PASSWORD")
PAGE_ID = os.environ.get("PAGE_ID")


test_keywords = ['SAT']
def fetch_articles(source):
    try:
        response = requests.get(source['url'])
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []

        # Get selectors from source in config.json
        name = source['name']
        article_selector = source['selectors']['article']
        title_selector = source['selectors']['title']
        link_selector = source['selectors']['link']
        image_selector = source['selectors']['image']
        title_attr = source['selectors'].get('title_attr', 'text')
        link_attr = source['selectors'].get('link_attr', 'href')
        image_attr = source['selectors'].get('image_attr', 'src')

        for item in soup.select(article_selector):
            title = extract_content(item, title_selector, title_attr)
            link = extract_content(item, link_selector, link_attr)
            image_url = extract_content(item, image_selector, image_attr)
            
            if title and link and any(keyword.lower() in title.lower() for keyword in test_keywords):
                articles.append({
                    'title': title,
                    'link': link,
                    'image_url': image_url,
                    'source': source['url'],
                    'source_name': name
                })

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

def extract_content(item, selector, attribute=None):
    element = item.select_one(selector)
    if element:
        return element[attribute] if attribute != 'text' else element.get_text(strip=True)
    return None

# def get_article_content(source, article_link):
#     response = requests.get(article_link)
#     response.raise_for_status()
#     soup = BeautifulSoup(response.content, 'html.parser')

#     text_selector = source['selectors']['text']
#     heading_selector = source['selectors']['headings']

#     paragraphs = [p.get_text(strip=True) for p in soup.find_all(text_selector)]

#     headings = [h.get_text(strip=True) for h in soup.select(heading_selector)]
#     content = []
#     content.append({
#         'headings': headings,
#         'text': paragraphs
#     })
#     return content

def post_to_wordpress(articles, wp_client, page_id):
    post = WordPressPost()
    first_article = articles[0]
    post.title = first_article['title']
    post.content = f"""
        <a href='{first_article['link']}' target='_blank' style='text-decoration: none; color: inherit;'>
            <div class='card' style='width: 18rem; margin: 10px auto; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <img class='card-img-top' src='{first_article['image_url']}' alt='Card image cap' style='width: 100%; height: auto;'>
                <div class='card-body' style='padding: 15px;'>
                    <h5 class='card-title' style='font-size: 1.25rem; margin-bottom: 10px;'>{first_article['title']}</h5>
                    <h4 class='card-source' style='font-size: 1rem; margin-bottom: 5px;'>{first_article['source_name']}</h4>
                </div>
            </div>
        </a>
        """
        
    post.terms_names = {
        'post_tag': ['SAT'],
        'category': ['Tests']
    }
    post.post_status = 'publish'
    wp_client.call(NewPost(post))
    print(f"Posted: {first_article['title']}")
    # cards_html = ""
    # first_article = articles[0]
    # card_html = f"""
    #     <a href='{first_article['link']}' target='_blank' style='text-decoration: none; color: inherit;'>
    #         <div class='card' style='width: 18rem; margin: 10px auto; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
    #             <img class='card-img-top' src='{first_article['image_url']}' alt='Card image cap' style='width: 100%; height: auto;'>
    #             <div class='card-body' style='padding: 15px;'>
    #                 <h5 class='card-title' style='font-size: 1.25rem; margin-bottom: 10px;'>{first_article['title']}</h5>
    #             </div>
    #         </div>
    #     </a>
    #     """
    # cards_html += card_html
    
    # pages = wp_client.call(GetPosts({'post_type': 'page', 'post_status': 'publish'}))
    # page = next((p for p in pages if p.id == page_id), None)

    # if page:
    #     # Update the page content with the cards
    #     page.content = cards_html

    #     # Save the updated page
    #     wp_client.call(EditPost(page))
    #     print(f"Updated page with ID {page_id} with {len(articles)} cards")
    # else:
    #     print(f"Page with ID {page_id} not found")

    


def main():
    with open('config.json') as f:
        config = json.load(f)
    
    all_articles = []
    
    for source in config['sources']:
        articles = fetch_articles(source)
        all_articles.extend(articles)
    # content = get_article_content(source, all_articles[0]['link'])
    # for stuff in content:
    #     print(f"Title: {all_articles[0]['title']}, Paragraphs: {stuff['text']}, Headings: {stuff['headings']}")

    print(f"Found {len(all_articles)} articles")
    wp_client = Client('https://highschoolnote.com/xmlrpc.php', WP_USERNAME, WP_PASSWORD)
    for article in all_articles:
        print(f"Title: {article['title']}, Link: {article['link']}, Image: {article['image_url']}")
    post_to_wordpress(all_articles, wp_client, PAGE_ID)
    

main()