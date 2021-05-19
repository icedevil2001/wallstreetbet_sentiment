
import pickle
import praw
from textblob import TextBlob 
import re
# import requests
from collections import defaultdict
from config import Config

# https://www.nasdaq.com/market-activity/stocks/screener?exchange=nasdaq&letter=0&render=download

def loadTicker(blacklist=[]):
    ticker_list  = []
    with open('Misc/tickers.txt') as tickers:
        for ticker in tickers:
            if ticker in blacklist: continue
            ticker_list.append(ticker.upper())
    print(f'Loaded {len(ticker_list)} stocks')
    return ticker_list

class SubredditScraper:

    def __init__(self, subobj, subreditt, sort='new', limit=10, stocklist=loadTicker()):
        self.subobj = subobj
        self.sub = subreditt.lower()
        self.sort = self.sortSub(sort)
        self.limit = limit
        self.stocklist = stocklist

        print(f'SubredditScraper instance created with values\n'
            f'sub = {subreditt}, sort = {sort}, lim = {limit}')
    
    def sortSub(self, sort):
        if sort.lower() in ['controversial', 'gilded', 'hot', 'new', 'rising', 'top' ]:
            return sort.lower()
        else:
            raise ValueError(f"{sort} is invaild: Select from['new','top', 'hot', 'raising']")
    
    def subReddit(self):
        subreddit = self.subobj.subreddit(self.sub)
        subr = getattr(subreddit, self.sort, None)
        print('**', subr)
        if subr is None:
            raise ValueError(f'{self.sort} is invaild')
        else:
            return subr(limit=self.limit)

    def scrap_comments(self, id, limit=0):
        subcommons = self.subobj.submission(id)
        subcommons.commonts.replace_more(limit=limit)
        for comment in subcommons:
            cleantext = CleanComment(comment)

            yield cleantext.cleanedText()
           
#   attrs = ['id', 'title', 'link_flair_text','url','num_comments', 'comments', 'view_count', 'upvote', 'upvote_ratio', 'score', 'downs']

    def getPost(self):
        stockTickers = defaultdict(dict)
        print(f'Collecting information from r/{self.sub}.')
        mentionedStocks = []
        i = 0
        for post in self.subReddit():
            if post.link_flair_text != 'Meme':
                # print(post.title)
                for stock in self.stocklist:
                    
                    found = False
                    if re.search(r'\s+\$?' + stock + r'\$?\s+', post.title):
                        found = True 
                    elif re.search(r'{}\s+?'.format(stock),  post.title):
                        found = True 
                    else:
                        continue 
                    if found:
                        print(f"FOUND {stock}")
                        stockTickers[stock][post.id] =  (post.permalink, post.ups, post.downs, post.num_comments, stock)
        for stock in stockTickers:
            if (len( [stock]) > 0):
                for post in stockTickers[stock]:
                    mentionedStocks.append(stockTickers[stock][post]) 
        print(stockTickers)
        return stockTickers
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


class getStock:
    def __init__(self, text):
        self.text = text
    
    def get_cashtag(self):
        cashtags = list(set(filter(lambda word: word.upper().startswith('$'), self.text)))
        if len(cashtags)> 0:
            return cashtags
        return None

class CleanComment:
    def __init__(self, text):
        self.text = text

    def removeHTTP(self):
        '''
        remove URLs and unwanted characters
        '''
        regx = re.compile('[\(\n)/$\(/r)(\[Poof\])]+')
        http = re.compile('(http.+?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+|http.:(?:[-\w.]|(?:%[\da-fA-F]{2}))+)')
        for pattern in [regx, http]:
            self.text = pattern.sub('',str(self.text))
        return self.text

    def deEmojify(self):
        '''
        remove Emojify
        '''
        regrex_pattern = re.compile(pattern = "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                            "]+", flags = re.UNICODE)
        return regrex_pattern.sub(r'',self.text)

    def cleanedText(self):
        '''
        Final cleaned text
        '''
        if self.text in ['[remove]', '[deleted]']:
            return None
        else:
            self.text = self.deEmojify()
            self.text = self.clean_text()
        return self.text
        

def get_sentiment(text):
  text = TextBlob( clean_body(text) )
  sentiment = text.sentiment
  return {'polarity': round(sentiment.polarity,3), "subjectivity": round(sentiment.subjectivity,3)}

def getcomments(id):
  sub = reddit.submission(id=id)
  sub.comments.replace_more(limit=0)
  tmp = []
  for x in sub.comments:

    clean_text = clean_body(x.body)
    if not clean_text:
      continue
    sent = get_sentiment(clean_text)
    if sent:
      tmp.append( (x.id, x.body, sent) )
    else:
      print(x.body)

  return tmp

if __name__ == "__main__":
    SUBRREBBIT = 'wallstreetbets'
    LIMIT = 10 
    reddit = praw.Reddit(**Config.metadata())
    stocklist = loadTicker()
    for sub in SubredditScraper(reddit, SUBRREBBIT,  sort='top', limit=LIMIT, stocklist=stocklist).getPost():
        print(sub)
