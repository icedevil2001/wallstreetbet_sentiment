
from os import link
import pickle
import praw
from praw.reddit import Subreddit
from textblob import TextBlob 
import re
# import requests
from collections import defaultdict
from config import Config
import pandas as pd
from pathlib import Path

from datetime import datetime

## TODO: add vars to argparse 
## -------------------------------------- ##
reddit = praw.Reddit(**Config.metadata())
subreddit = 'wallstreetbets'
limit = 1e6
comment_level = 1
sortby = 'gilded' #'hot' ## ['controversial', 'gilded', 'hot', 'new', 'rising', 'top' ]
time_filter = 'all' #'all' ##sortby = controversial ==> time_tiler = Can be one of: all, day, hour, month, week, year (default: all).

## -------------------------------------- ##

def loadTicker(blacklist=[]):
    ticker_list  = []
    with open('Misc/tickers.txt') as tickers:
        for ticker in tickers:
            ticker = ticker.strip()
            if ticker in blacklist: continue
            ticker_list.append(ticker.upper())
    print(f'Loaded {len(ticker_list)} stocks')
    return ticker_list


def clean_body(text):
  if text in ['[remove]', '[deleted]']:
    return None
  else:
    text = deEmojify(text)
    text = clean_text(text)
    return text
    
def clean_text(text):
  regx = re.compile('[\(\n)/$\(/r)(\[Poof\])]+')
  http = re.compile('(http.+?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+|http.:(?:[-\w.]|(?:%[\da-fA-F]{2}))+)')
  for pattern in [regx, http]:
    text = pattern.sub('',str(text))
  return text

# def deEmojify(text):
#     regrex_pattern = re.compile(pattern = "["
#         u"\U0001F600-\U0001F64F"  # emoticons
#         u"\U0001F300-\U0001F5FF"  # symbols & pictographs
#         u"\U0001F680-\U0001F6FF"  # transport & map symbols
#         u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
#                            "]+", flags = re.UNICODE)
#     return regrex_pattern.sub(r'',text)

def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')

def get_sentiment(text):
  text = TextBlob( clean_body(text) )
  sentiment = text.sentiment
  return sentiment
#   return {'polarity': round(sentiment.polarity,3), "subjectivity": round(sentiment.subjectivity,3)}

class getStock:
    def __init__(self, text, whitelist, blacklist_stocks):
        self.text = text
        self.stock_whitelist = whitelist
        self.blacklist_stocks = blacklist_stocks
    def getCashTag(self):
        # cashtags = set(filter(lambda word: word.upper().startswith('$'), self.text.strip().split()))
        cashtags = re.search(r'(\$[A-Z\.]+|[A-Z\.]{1,5}\$)', self.text)
        if cashtags:
            return [cashtags.group(1).replace('$','')]

    def fromList(self):
        # potential_stocks = list(set(filter(lambda word: word.upper() if len(word)<=5 else False, self.text.split())))
        # for stock in potential_stocks:
        stocks = set()
        for word in self.text.split():
            
            if len(word)<=5: 
                
                if word in self.stock_whitelist:
                    if word in self.blacklist_stocks:
                        continue
                    stocks.add(word)
        return list(stocks)

    
    def findStock(self):
        found = self.fromList()
        if len(found)>0:
            return found
        elif self.getCashTag():
            return self.getCashTag()
        else:
            return None

def topic_sortby(subreddit_odj, sortby, limit, time_filter):
    # reddit.subreddit(subreddit)
    if sortby == 'controversial':
        subreddit_sorted = getattr(subreddit_odj ,'controversial', None)
        if subreddit_sorted is None:
            raise ValueError(f'Can not sort by {sortby}')
        print("time_filter", time_filter)
        return subreddit_sorted(time_filter)
    else:
        subreddit_sorted = getattr(subreddit_odj ,sortby, None)
        if subreddit_sorted is None:
            raise ValueError(f'Can not sort by {sortby}')
        return subreddit_sorted(limit=limit)


def agg_stocks(x):
    stats = {
        'num_mentioned': len(x), 
        'polarity': x['polarity'].mean(),
        'subjectivity': x['subjectivity'].mean()
    }
    return pd.Series(stats, index=stats.keys())

#### main #### 


tags = ['Daily Discussion', 'Discussion', 'DD','YOLO' ]

#['children', 'comments', 'count', 'depth', 'id',
#  'name', 'parent_id', 'parse', 'submission']

## TODO: add blacklist to a file
stock_blacklist = [ "A", "AND", "THE", "YOLO", "TOS", "CEO", "CFO", "CTO", "DD", "BTFD", "WSB", "OK", "RH",
      "KYS", "FD", "TYS", "US", "USA", "IT", "ATH", "RIP", "BMW", "GDP",
      "OTM", "ATM", "ITM", "IMO", "LOL", "DOJ", "BE", "PR", "PC", "ICE",
      "TYS", "ISIS", "PRAY", "PT", "FBI", "SEC", "GOD", "NOT", "POS", "COD",
      "AYYMD", "FOMO", "TL;DR", "EDIT", "STILL", "LGMA", "WTF", "RAW", "PM",
      "LMAO", "LMFAO", "ROFL", "EZ", "RED", "BEZOS", "TICK", "IS", "DOW"
      "AM", "PM", "LPT", "GOAT", "FL", "CA", "IL", "PDFUA", "MACD", "HQ",
      "OP", "DJIA", "PS", "AH", "TL", "DR", "JAN", "FEB", "JUL", "AUG",
      "SEP", "SEPT", "OCT", "NOV", "DEC", "FDA", "IV", "ER", "IPO", "RISE"
      "IPA", "URL", "MILF", "BUT", "SSN", "FIFA", "USD", "CPU", "AT",
      "GG", "ELON", 'HE', 'HES']

 
stock_whitelist = loadTicker()

raw_output_fn = Path('data/raw_wallstreetbets_scaped_data.plk')

post_ids  = None 
if raw_output_fn.exists():
    df1 = pd.read_pickle(str(raw_output_fn))
    post_ids = list(df1.post_id.unique())

data = []

for sub in topic_sortby(reddit.subreddit(subreddit),sortby, limit, time_filter): #reddit.subreddit(subreddit).hot(limit=limit):
    try:
        sub.link_flair_text
    except:
        continue
    if sub.link_flair_text in tags: 
        dt = datetime.fromtimestamp(sub.created_utc)
        if post_ids and sub.id in post_ids and dt.date() != datetime.today().date():
            print(f'SKIPPED: [{dt.date()}] - {sub.title}')
            continue 

        
        print(f'POST: [{dt.date()}]: {sub.title}\nNumber of comments: {sub.num_comments}\n')
        
        subcomments = reddit.submission(sub.id)
        subcomments.comments.replace_more(limit=comment_level)
        #print('-'*20)
        #print('Comments')
        #print('-'*20)

        for num,comment in enumerate(subcomments.comments):
           
            isStock = getStock(comment.body, stock_whitelist, stock_blacklist).findStock()
      
            if isStock :
                # print('-'*50)
                sentiment = get_sentiment(comment.body)
                # print('YAY - FOUND:', isStock, sentiment)

                for stock in isStock:
                    data.append( 
                        (   
                            sub.created_utc, sub.id,
                            stock, sentiment.polarity,
                            sentiment.subjectivity,
                            clean_body(comment.body.strip()), comment.id
                        ) 
                        )

            # if num> 101: 
            #     print('BREAK!!')
            #     break



df = pd.DataFrame(data, columns=['datetime_utc','post_id', 'ticker', 'polarity', 'subjectivity', 'body', 'id'])



if raw_output_fn.exists():
    df1 = pd.read_pickle(str(raw_output_fn))
    df = pd.concat([df, df1], ignore_index=True).sort_values('datetime_utc')
df = df.drop_duplicates()

df.to_pickle(raw_output_fn, )
df['datetime'] = df.datetime_utc.apply(datetime.fromtimestamp)
df = df.set_index('datetime')
df_agg = (
    df.groupby(
        [pd.Grouper(freq='D'),'ticker']
        ).apply(
            agg_stocks
            ).sort_values(
                by='num_mentioned',
                ascending=False)
                )
df_agg.to_csv('data/aggrated_data.tsv', sep='\t')

print('#'*50)
print(df_agg)
print('#'*50)