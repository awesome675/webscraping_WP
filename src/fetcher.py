import requests
import os
from os.path import join, dirname
from bs4 import BeautifulSoup
import json
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts, EditPost
from dotenv import load_dotenv
import random


load_dotenv()

WP_USERNAME = os.environ.get("WP_USERNAME")
WP_PASSWORD = os.environ.get("WP_PASSWORD")

posted_file = 'posted.txt'
test_keywords = ['']

def load_posted_articles():
    if os.path.exists(posted_file):
        with open(posted_file, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_posted_articles(posted_articles):
    with open(posted_file, 'a') as f:
        for link in posted_articles:
            f.write(f"{link}\n")
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
        image_attr = source['selectors'].get('img_attr', 'src')
        default_url = 'https://www.bankrate.com/2014/05/26174958/Reasons-to-go-to-college.jpg'
        base_url = source.get('base_url', '')

        for item in soup.select(article_selector):
            title = extract_content(item, title_selector, title_attr)
            link = extract_content(item, link_selector, link_attr)
            image_url = extract_content(item, image_selector, image_attr)

            if link and not link.startswith('http'):
                link = base_url + link

            if image_url and not image_url.startswith('http'):
                image_url = base_url + image_url

            if not image_url:
                image_url = default_url
            
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



def post_to_wordpress(article, wp_client):

    
    post = WordPressPost()
    post.title = article['title']
    post.content = f"""
    <a href='{article['link']}' target='_blank' style='text-decoration: none; color: inherit;'>
        <div class='card' style='width: 18rem; margin: 10px auto; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <img class='card-img-top' src='{article['image_url']}' alt='Card image cap' style='width: 100%; height: auto;'>
            <div class='card-body' style='padding: 15px;'>
                <h5 class='card-title' style='font-size: 1.25rem; margin-bottom: 10px;'>{article['title']}</h5>
                <h4 class='card-source' style='font-size: 1rem; margin-bottom: 5px;'>{article['source_name']}</h4>
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
    print(f"Posted: {article['title']}")


    


def main():
    posted_articles = load_posted_articles()


    with open('config.json') as f:
        config = json.load(f)
    
    all_new_articles = []
    
    for source in config['sources']:
        articles = fetch_articles(source)
        all_new_articles.extend(articles)
    
    new_articles_to_post = [article for article in all_new_articles if article['link'] not in posted_articles]
    if not new_articles_to_post:
        print('No more articles')
        return
    random.shuffle(new_articles_to_post)
    articles_posted = new_articles_to_post[:5]

    wp_client = Client('https://highschoolnote.com/xmlrpc.php', WP_USERNAME, WP_PASSWORD)
    for article in articles_posted:
        print(f"Title: {article['title']}, Link: {article['link']}, Image: {article['image_url']}, Source: {article['source_name']}")
        post_to_wordpress(article, wp_client)
        posted_articles.add(article['link'])
    
    save_posted_articles([article['link'] for article in articles_posted])

    

main()