from deep_translator import GoogleTranslator
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import re
import nltk
from collections import Counter
# Removed subprocess, os, glob imports as they were only for video
# Removed faster_whisper import

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize

try:
    nltk.download('punkt')
    nltk.download('vader_lexicon')
except:
    pass


sentiment_analyzer = SentimentIntensityAnalyzer()

LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te"
}

def translate_text(text, target_lang="en"):
    try:
        if not text or target_lang == "en":
            return text
        max_chars = 4900
        if len(text) > max_chars:
            chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
            translated_chunks = [GoogleTranslator(source='auto', target=target_lang).translate(chunk) for chunk in chunks]
            return ' '.join(translated_chunks)
        else:
            return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# Removed whisper_model initialization

GNEWS_API_KEY = "d8d0c9b247a6332d96d9973996999821" # Consider moving to environment variables
GNEWS_ENDPOINT = "https://gnews.io/api/v4/search"

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'<.*?>', '', text)
    return text.strip()

def is_video_url(url):
    return bool(re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', url))

def extract_main_content(soup):
    blacklist = re.compile(r'(footer|header|nav|sidebar|ads|sponsored|related)', re.I)
    article_text = ""
    for tag in soup.find_all(['article', 'main', 'div']):
        if tag.get("class") and any(blacklist.search(cls) for cls in tag.get("class", [])):
            continue
        paragraphs = tag.find_all('p')
        text = ' '.join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 30])
        link_count = sum(1 for _ in tag.find_all('a'))
        word_count = len(text.split())
        if word_count < 100 or link_count > word_count // 5:
            continue
        if len(text) > len(article_text):
            article_text = text
    return clean_text(article_text)

def scrape_article(url, topic=""):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.text.strip() if title_tag else "Untitled"
        if topic and not any(keyword.lower() in title.lower() for keyword in topic.split()):
            return None
        content = extract_main_content(soup)
        if len(content) < 200:
            return None
        return {"title": title, "content": content, "url": url}
    except:
        return None

def fetch_news(interests, max_articles_per_interest=5):
    articles = []
    for interest in interests:
        params = {"q": interest, "token": GNEWS_API_KEY, "lang": "en", "max": max_articles_per_interest}
        try:
            res = requests.get(GNEWS_ENDPOINT, params=params, timeout=10)
            data = res.json()
            for item in data.get("articles", []):
                item['interest_category'] = interest
                articles.append(item)
        except Exception as e:
            print(f"Failed to fetch GNews for {interest}: {e}")
    return articles

def scrape_articles(articles):
    urls = [a['url'] for a in articles if 'url' in a]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        scraped = list(executor.map(lambda u: scrape_article(u, articles[urls.index(u)]['interest_category']), urls))
    result = []
    for i, r in enumerate(scraped):
        if r:
            r['interest_category'] = articles[i]['interest_category']
            result.append(r)
    return result

def simple_extractive_summarize(text, max_sentences=3):
    if len(text) < 100:
        return text
    sentences = list(dict.fromkeys(sent_tokenize(text)))
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    freq = Counter(words)
    scored = [(sum(freq.get(w, 0) for w in re.findall(r'\b[a-zA-Z]{3,}\b', s.lower())), s) for s in sentences]
    top = sorted(scored, reverse=True)[:max_sentences]
    top_sorted = sorted(top, key=lambda x: sentences.index(x[1]))
    return ' '.join(s for _, s in top_sorted)

def analyze_sentiment(text):
    scores = sentiment_analyzer.polarity_scores(text)
    c = scores['compound']
    if c >= 0.3:
        return "positive"
    elif c <= -0.3:
        return "negative"
    return "neutral"

def summarize_articles(grouped):
    summaries = {}
    for interest, arts in grouped.items():
        full_text = ' '.join([a['content'] for a in arts])
        summary = simple_extractive_summarize(full_text, max_sentences=5)
        sentiment = analyze_sentiment(full_text)
        summaries[interest] = {
            "headline": f"Summary for {interest.title()}",
            "summary": summary,
            "sentiment": sentiment,
            "sources": [{"title": a['title'], "url": a['url']} for a in arts]
        }
    return summaries

def group_by_interest(articles):
    grouped = {}
    for a in articles:
        key = a.get('interest_category', 'general')
        grouped.setdefault(key, []).append(a)
    return grouped

def get_news_summaries(interests, max_articles_per_category=5):
    articles = fetch_news(interests, max_articles_per_category)
    scraped = scrape_articles(articles)
    if not scraped:
        return {"error": "No relevant articles found."}
    grouped = group_by_interest(scraped)
    summaries = summarize_articles(grouped)
    return {"summaries": summaries, "articles": scraped}

def get_news_chat_summary(topic, num_articles=4, target_lang="en"):
    result = get_news_summaries([topic], max_articles_per_category=num_articles)
    if "error" in result:
        error_msg = f"Could not find articles on '{topic}'."
        return translate_text(error_msg, target_lang)
    summaries = result["summaries"]
    data = summaries.get(topic, {})
    if not data:
        error_msg = f"No summary found for '{topic}'."
        return translate_text(error_msg, target_lang)

    if target_lang != "en":
        try:
            headline = translate_text(data['headline'], target_lang)
            summary = translate_text(data['summary'], target_lang)
            sentiment_label = translate_text("Sentiment: ", target_lang)
            sentiment = translate_text(data['sentiment'].title(), target_lang)
            sources_label = translate_text("Sources:", target_lang)
        except:
            sentiment_label = "Sentiment: "
            sentiment = data['sentiment'].title()
            sources_label = "Sources:"
    else:
        headline = data['headline']
        summary = data['summary']
        sentiment_label = "Sentiment: "
        sentiment = data['sentiment'].title()
        sources_label = "Sources:"

    msg = f"📰 {headline}\n\n"
    msg += f"{summary}\n\n"
    msg += f"{sentiment_label}{sentiment}\n\n"
    msg += sources_label + "\n" + '\n'.join([f"- [{s['title']}]({s['url']})" for s in data['sources']])
    return msg

# Removed download_audio function
# Removed transcribe_with_whisper function
# Removed extract_video_info function
# Removed get_content_summary function