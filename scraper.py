
import pickle
import praw
from textblob import TextBlob 
import re
# import requests
from collections import defaultdict
from config import Config

SUBRREBBIT = 'wallstreetbets'
LIMIT = 10 

reddit = praw.Reddit(**Config.client_id)


def stock(x):
  r = re.search('^(\$[A-Z\.]+)', str(x), re.I)
  if r:
    return r.group(1)


class SubredditScraper:

    def __init__(self, subreditt, sort='new', limit=10):
        self.sub = subreditt.lower()
        self.sort = self.sortSub(sort)
        self.limit = limit

        print(f'SubredditScraper instance created with values\n'
            f'sub = {subreditt}, sort = {sort}, lim = {limit}')
    
    def sortSub(self, sort):
        if sort.lower() in ['new','top', 'hot', 'raising']:
            return sort.lower()
        else:
            raise ValueError(f"{sort} is invaild: Select from['new','top', 'hot', 'raising']")
    
    def subReddit(self):
        subreddit = reddit.subreddit(self.sub)
        subr = getattr(subreddit, self.sort, None)
        if subr is None:
            raise ValueError(f'{self.sort} is invaild')
        else:
            return subr

    def loadTicker(self):
        tmp  = []
        with open('Misc/tickers.txt') as tickers:
            for ticker in tickers:
                tmp.appand(ticker)
        return tmp

    

    def getPost(self):

        subreddit = self.subReddit()

        print(f'Collecting information from r/{self.sub}.')
        mentionedStocks = []
        i = 0
        for post in subreddit:
            if post.link_flair_text != 'Meme':
                for stock in stockTickers.keys():
                    if (re.search(r'\s+\$?' + stock + r'\$?\s+', post.selftext) or re.search(r'\s+\$?' + stock + r'\$?\s+',  post.title)):
                        stockTickers[stock][post.id] = StockPost(post.id, post.permalink, post.ups, post.downs, post.num_comments, stock)
        for stock in stockTickers:
            if (len( [stock]) > 0):
                for post in stockTickers[stock]:
                    mentionedStocks.append(stockTickers[stock][post]) 
        return (mentionedStocks)
        # json_object = json.dump(
            # mentionedStocks, 
            # default=jsonDefEncoder
            # )  
         
        # print(json_object)  


        # headers = {'Content-type':'application/json', 'Accept':'application/json', 'Flamingo-Signature': "" }
        # r = requests.post("https://wsbstonks.azurewebsites.net/api/RedditPostsAdmin", data=json_object,  headers=headers)
        # print(r.status_code)
        # print(r.text)
        # return json_object

    def as_dict(self):
      return [x.__dict__ for x in self.get_posts()]

