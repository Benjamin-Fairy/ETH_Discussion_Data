import os
import json
import re
from datetime import datetime
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, 'data_collect')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
OUTPUT_FILE = os.path.join(DOCS_DIR, 'data_summary.json')

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'[\r\n\t\\]+', ' ', text)

def process_daily_data():
    summary_data = []

    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    # Fetch ETH historical data from Yahoo Finance (1 year lookback is usually enough)
    print("Fetching ETH price data from Yahoo Finance...")
    eth_ticker = yf.Ticker("ETH-USD")
    eth_hist = eth_ticker.history(period="1y")
    # Convert index to simple YYYY-MM-DD string for easy matching
    eth_hist.index = eth_hist.index.strftime('%Y-%m-%d')

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(DATA_DIR, filename)
        date_str = filename.replace('ETH_data_', '').replace('.json', '')

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            daily_posts = json.load(f)

        volume = len(daily_posts)
        sentiment_scores = {'bullish': 0, 'bearish': 0, 'neutral': 0}

        for post in daily_posts:
            content = clean_text(post.get('content', ''))
            tendency = post.get('tendency', 0)
            if tendency == 1:
                sentiment_scores['bullish'] += 1
            elif tendency == 2:
                sentiment_scores['bearish'] += 1
            else:
                sentiment_scores['neutral'] += 1

        # Match price data for the specific date
        closing_price = None
        if date_str in eth_hist.index:
            # Get the closing price and round to 2 decimal places
            closing_price = round(float(eth_hist.loc[date_str]['Close']), 2)

        formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')

        summary_data.append({
            "timestamp": formatted_date,
            "volume": volume,
            "sentiment": sentiment_scores,
            "price": closing_price  # <-- 新增的价格字段
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed and saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    process_daily_data()