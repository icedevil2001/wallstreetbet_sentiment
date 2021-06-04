import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime 
import yfinance as yf

def download_stock(stock_list, start_date, end_date):
   
    df = yf.download(stock_list, start=start_date, end=end_date)
    df = df.drop(['High', 'Low', 'Open','Close','Volume'], axis=1)
    df = df.rename(columns={'Adj Close': "adj_close"})
    df = df.droplevel(level=0, axis=1)
    df = df.apply(normalizion2, axis=0)
    #df = df.apply(as_percentage, axis=0)

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

df = pd.read_pickle('data/raw_wallstreetbets_scaped_data.plk')
#df['datetime'] = pd.DatetimeIndex(df.datetime_utc)
df['datetime'] = df.datetime_utc.apply(datetime.fromtimestamp)

df = df.set_index('datetime')


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
                     subplot_titles = ['Stock Price action (normalized)', 'WallStreetBets Stock mentions']
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
fig.update_layout({
    "barmode":"stack",
    # 'updatemenus':updatemenus
    }, 
    title_text = 'WallStreetBets reddit scraper',
    xaxis2_rangeslider_visible =True 
)
fig.update_xaxes(
    # rangeslider_visible=True,
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1d", step="day", stepmode="backward"),
            dict(count=1, label="1w", step="day", stepmode="backward"),
            dict(count=1, label="1m", step="month", stepmode="backward"),
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
#fig.write_html('wallstreetbets_stock_mentions.html')

# print(df1)

