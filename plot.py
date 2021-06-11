import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime, timedelta
import yfinance as yf

from collections import Counter

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from matplotlib import pyplot as plt
from PIL import Image

blacklisted_words = set(['he','think', 'hes', 'o', 'n','t','tt',
'T' ,'a', 'in', 'the', 'to', 'the', 'be', 'and', 'nt', 'n', 'ae', 'g', 'ut']
)

def download_stock(stock_list, start_date, end_date):
   
    df = yf.download(stock_list, start=start_date, end=end_date)
    df = df.drop(['High', 'Low', 'Open','Close','Volume'], axis=1)
    df = df.rename(columns={'Adj Close': "adj_close"})
    df = df.droplevel(level=0, axis=1)
    df = df.apply(normalize_with_last, axis=0)
    # df = df.apply(as_percentage, axis=0)

    df = df.reset_index().rename(columns={'Date':'datetime'})
    return df

def as_percentage(arry):
    '''
    df of stock prices
    '''
    return 100 * ((arry / arry.min()))

def normalizion(arry):
    '''
    linear remapping
    '''
    return ( (arry - arry.min()) / (arry.max() - arry.min()) )

def normalizion2(arry):
    return (arry / (arry.max() - arry.min()))

def normalize_with_last(arry):
    return (arry/ arry.values[0])


# def word_freq(text, blacklist_words):
#     frq =  Counter([word.strip().lower() for word in text.strip().split() if not word.strip().lower() in blacklist_words])
#     (frq.pop(w) for w in blacklist_words)
#     print(frq)
#     return frq

def words_of_the_day(comments, blacklisted_words=[]):

    mask = np.array(Image.open("Misc/ROCKET_NEW.png"))
    image_colors = ImageColorGenerator(mask)
    stopwords = set(STOPWORDS)
    (stopwords.add(w) for w in blacklisted_words)

    wc = WordCloud(
        background_color="white", max_words=4000,
        mask=mask, 
        stopwords=stopwords, 
        contour_width=1, 
        contour_color='steelblue'
        )

    fig, ax = plt.subplots(1, figsize=(10,10))
    wordfreq = ' '.join(comments)
    wc.generate(wordfreq)
   
    ax.imshow(wc.recolor(color_func=image_colors), cmap=plt.cm.gray,interpolation="bilinear")
    ax.axis('off')
    fig.savefig('Words_of_day.png')
    #fig.show()

df = pd.read_pickle('data/raw_wallstreetbets_scaped_data.plk')
#df['datetime'] = pd.DatetimeIndex(df.datetime_utc)
df['datetime'] = df.datetime_utc.apply(datetime.fromtimestamp)
#df['date'] = df.datetime.apply(lambda x: x.date())

df = df.set_index('datetime')
today = pd.to_datetime('today')
## Filter for last 6month
days = 6 * 30 ## months * days == 180days
td = today - timedelta(days)  ## time delta
df = df.loc[df.index.date >= td ]
print(today)

## Filter 
total_mensions = df.ticker.value_counts()
q = total_mensions.quantile(0.985)
stock_list = list(total_mensions[total_mensions>=q].index)

df1 = df.groupby([pd.Grouper(freq='D'),'ticker']).size()
df1 = df1.rename('num_of_mentions').reset_index()
df1 = df1.loc[df1.ticker.isin(stock_list)]
# stock_list = list(df1.ticker.unique())
start_date = df1.datetime.min()
end_date = df1.datetime.max()

## Download stock prices
st = download_stock(stock_list, start_date, end_date)
st_m = pd.melt(
    st,
    id_vars='datetime', 
    value_vars=st.iloc[:, 1:].columns,
    value_name='price',
    var_name=['ticker']
)

dfx = st_m.merge(df1, on=['datetime', 'ticker'], how='outer')

fig1 = px.line(dfx, x='datetime', y='price', color='ticker')
fig2 = px.bar(dfx, x='datetime', y='num_of_mentions',color='ticker' )

fig = make_subplots(rows=2, cols=1,
                     shared_xaxes=True,
                     vertical_spacing=0.1,
                     subplot_titles = ['Stock Action ', 'WallStreetBets Stock mentions']
                     )

for p in fig1['data']:
    fig.add_trace(p, row=1, col=1)

for p in fig2['data']:
    fig.add_trace(p, row=2, col=1)

### Create buttons for drop down menu

# buttons = []

# buttons.append(dict(
#                  label = 'ALL',
#                  method = 'update',
#                  args = [{'visible': [True for _ in range(len(dfx.ticker))]},
#                      {'title': 'ALL'}])
# )

# for i, label in enumerate(dfx.ticker.unique()):
#     visibility = [i==j for j in range(len(dfx.ticker))]
#     button = dict(
#                  label =  label,
#                  method = 'update',
#                  args = [{'visible': visibility},
#                      {'title': label}])
#     buttons.append(button)


# updatemenus = [
#     dict(active=-1,
#          x=-0.15,
#          buttons=buttons
#     )
# ]

# fig['layout']['updatemenus'] = updatemenus

updatemenus=[dict(
            type="buttons",
            direction="left",
            buttons=[
                dict(label="Linear Scale",  
                    method="relayout", 
                    args=[{"yaxis.type": "linear", "yaxis2.type": "linear"}]
                    ),
                dict(label="Log Scale", 
                    method="relayout", 
                    args=[{"yaxis.type": "log", "yaxis2.type": "log"}],
                    ),
                    ])]


fig.update_layout(
    barmode = "stack",
    updatemenus = updatemenus,
    title_text = 'WallStreetBets reddit scraper',
    xaxis2_rangeslider_visible =True,
    yaxis1=dict(
        autorange = True,
        # type = 'log',
        fixedrange= False,
        title='Normalized (price / price @ day0)'
    ),
    yaxis2=dict(
       autorange = True,
    #    type='log',
       fixedrange= False,
       title='Num of mentions (count)'
    ),
)
fig.update_xaxes(
    # rangeslider_visible=True,

    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1d", step="day", stepmode="backward"),
            dict(count=7, label="1w", step="day", stepmode="backward"),
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=2, label="2m", step="month", stepmode="backward"),
            # dict(count=6, label="6m", step="month", stepmode="backward"),
            # dict(count=1, label="YTD", step="year", stepmode="todate"),
            # dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])
    )
)
# fig.update_layout(height=600, width=600,
                #   title_text="Stacked Subplots with Shared X-Axes")
fig.show()
fig.write_html('wallstreetbets_stock_mentions.html')

# print(df1)

## Only shows words from today
words_of_the_day(df.loc[df.index.date == today].body.to_list(), blacklisted_words)