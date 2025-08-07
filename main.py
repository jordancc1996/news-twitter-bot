import os
import openai
import tweepy
import requests
import time
import json
import schedule
from datetime import datetime

class NewsTwitterBot:
    def __init__(self):
        # Initialize OpenAI
        self.openai_client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        
        # Initialize Twitter API
        self.twitter_client = tweepy.Client(
            bearer_token=os.environ['TWITTER_BEARER_TOKEN'],
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
            access_token=os.environ['TWITTER_ACCESS_TOKEN'],
            access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'],
            wait_on_rate_limit=True
        )
        
        self.news_api_key = os.environ['NEWS_API_KEY']
    
    def get_latest_news(self, topics=['technology', 'business'], max_articles=3):
        """Fetch latest news from NewsAPI"""
        articles = []
        
        for topic in topics:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': topic,
                'apiKey': self.news_api_key,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': max_articles
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                articles.extend(data.get('articles', []))
                
        return articles[:max_articles]
    
    def create_tweet(self, article):
        """Use OpenAI to create engaging tweet"""
        prompt = f"""
        Create a compelling tweet about this news article:
        
        Title: {article['title']}
        Description: {article['description']}
        URL: {article['url']}
        
        Requirements:
        - Under 280 characters
        - Include relevant hashtags
        - Make it engaging and informative
        - Include the article URL
        
        Just return the tweet text, nothing else.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheaper than GPT-4
                messages=[
                    {"role": "system", "content": "You are an expert social media manager who creates engaging tweets."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating tweet: {e}")
            return None
    
    def post_tweet(self, tweet_text):
        """Post tweet to Twitter"""
        try:
            response = self.twitter_client.create_tweet(text=tweet_text)
            print(f"✅ Posted: {tweet_text[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Error posting tweet: {e}")
            return False
    
    def run_news_cycle(self):
        """Main function to fetch news and tweet"""
        print(f"🔄 Starting news cycle at {datetime.now()}")
        
        topics = ['artificial intelligence', 'technology', 'startups']
        articles = self.get_latest_news(topics, max_articles=2)
        print(f"📰 Found {len(articles)} articles")
        
        posted_count = 0
        for article in articles:
            if not article.get('description'):
                continue
                
            # Generate tweet
            tweet_text = self.create_tweet(article)
            
            if tweet_text and self.post_tweet(tweet_text):
                posted_count += 1
                time.sleep(30)  # Wait 30 seconds between posts
                
                if posted_count >= 2:  # Limit posts per cycle
                    break
                    
        print(f"✨ Cycle complete. Posted {posted_count} tweets.")

# Main execution
if __name__ == "__main__":
    try:
        bot = NewsTwitterBot()
        
        # Run once immediately
        bot.run_news_cycle()
        
        # Then schedule to run every 2 hours
        schedule.every(2).hours.do(bot.run_news_cycle)
        
        print("🤖 Bot is running! Will post news every 2 hours.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"💥 Bot error: {e}")
