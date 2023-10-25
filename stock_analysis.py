import mplfinance as mpf
import numpy as np
import yfinance as yf
import argparse
import os

def calculate_bolling_bands(df):
  ### Bollinger Bands
    window = 20
    no_of_std = 2

    #Calculate rolling mean and standard deviation using number of days set above
    rolling_mean = df['Close'].rolling(window).mean()
    rolling_std = df['Close'].rolling(window).std()
    rolling_vol = df['Volume'].rolling(window).mean()

    #create two new DataFrame columns to hold values of upper and lower Bollinger bands
    df['MeanB'] = rolling_mean
    df['UpperB'] = rolling_mean + (rolling_std * no_of_std)
    df['LowerB'] = rolling_mean - (rolling_std * no_of_std)
    df['VolB'] = rolling_vol
    df['BandwidthB']  = (df['UpperB'] - df['LowerB']) / df['MeanB']
    df['PercentB'] = (df['Close'] - df['LowerB']) / (df['UpperB'] - df['LowerB'])


def calculate_moving_average_crossover(df, short_window=50, long_window=100):
    # Calculate the short-term moving average
    df['Short_MA'] = df['Close'].rolling(window=short_window).mean()

    # Calculate the long-term moving average
    df['Long_MA'] = df['Close'].rolling(window=long_window).mean()

    # Generate signals based on the crossover
    df['Signal_MA'] = 0
    df.loc[df['Short_MA'] > df['Long_MA'], 'Signal_MA'] = 1
    df.loc[df['Short_MA'] < df['Long_MA'], 'Signal_MA'] = -1

    # Calculate the positions (buy/sell) based on the signal change
    df['Position_MA'] = df['Signal_MA'].diff()  



def percentB_belowzero(percentB, price):
    signal = []
    previous = -1.0
    for date,value in percentB.items():
        if value < 0 and previous >= 0:
            signal.append(price[date]*0.99)
        else:
            signal.append(np.nan)
        previous = value
    return signal


def percentB_aboveone(percentB, price):
    signal = []
    previous = 2
    for date,value in percentB.items():
        if value > 1 and previous <= 1:
            signal.append(price[date]*1.01)
        else:
            signal.append(np.nan)
        previous = value
    return signal


def get_ticket_history_data(ticket_name):
    tickerData = yf.Ticker(ticket_name)
    df = tickerData.history(period='5y', interval='1d')
    return df

def move_to_result_directory(filename):
    dirpath = './img'
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    os.rename(f'./{filename}', f'./{dirpath}/{filename}')



def make_plots(sdf, ticket_name, low_signal_BB, high_signal_BB, low_signal_MA, high_signal_MA, lenght, tl=True):

    mystyle=mpf.make_mpf_style(base_mpf_style='ibd',rc={'axes.labelsize':'xx-small'})

    apds = [ mpf.make_addplot(sdf['UpperB'], color='blue', width=0.7, fill_between=dict(y1=sdf['UpperB'].values,y2=sdf['LowerB'].values, alpha=0.05, color='lime')),
        mpf.make_addplot(sdf['LowerB'], color='orange', width=0.7),
        mpf.make_addplot(sdf['Short_MA'], color='red', label="50 MA"),
        mpf.make_addplot(sdf['Long_MA'], color='green', label="100 MA")]

    if (np.isnan(low_signal_BB).all() == False):
        apds.append(mpf.make_addplot(low_signal_BB,type='scatter',markersize=50,marker='^', color="orange"))

    if (np.isnan(high_signal).all() == False):
        apds.append(mpf.make_addplot(high_signal_BB,type='scatter',markersize=50,marker='v', color='blue'))

    if (np.isnan(low_signal_MA).all() == False):
        apds.append(mpf.make_addplot(low_signal_MA,type='scatter',markersize=50, marker='^', color="green"))

    if (np.isnan(high_signal_MA).all() == False):
        apds.append(mpf.make_addplot(high_signal_MA,type='scatter',markersize=50,marker='v', color="red"))

    mpf.plot(sdf, addplot=apds, type='candle', style=mystyle, panel_ratios=(1,0.1), title=ticket_name, 
             figscale=1.5, figratio=(12,10), volume=True, savefig=dict(fname=f'{ticket_name}-{lenght}.png',dpi=1080,pad_inches=0.25), tight_layout=tl)    

    move_to_result_directory(f'{ticket_name}-{lenght}.png')



parser = argparse.ArgumentParser()

parser.add_argument("stock", type=str)
parser.add_argument("-s","--short-window-ma", type=int, action="store")
parser.add_argument("-l","--long-window-ma", type=int, action="store")

args = parser.parse_args()

df = get_ticket_history_data(args.stock)
calculate_bolling_bands(df)
if (args.short_window_ma == None) and (args.long_window_ma != None):
    calculate_moving_average_crossover(df, long_window=args.long_window_ma)
elif (args.short_window_ma != None) and (args.long_window_ma == None): 
    calculate_moving_average_crossover(df, short_window=args.short_window_ma)
elif  (args.short_window_ma != None) and (args.long_window_ma != None): 
    calculate_moving_average_crossover(df, short_window=args.short_window_ma, long_window=args.long_window_ma)
else:
    calculate_moving_average_crossover(df)

long_df = df[-360:-1]

low_signal  = percentB_belowzero(long_df['PercentB'], long_df['Close']) 
high_signal = percentB_aboveone(long_df['PercentB'], long_df['Close'])
low_signal_ma = percentB_belowzero(long_df['Position_MA'], long_df['Long_MA']) 
high_signal_ma = percentB_aboveone(long_df['Position_MA'], long_df['Long_MA'])

make_plots(long_df, args.stock,  low_signal, high_signal, low_signal_ma, high_signal_ma, '360d')

short_df = df[-30:-1]

low_signal  = percentB_belowzero(short_df['PercentB'], short_df['Close']) 
high_signal = percentB_aboveone(short_df['PercentB'], short_df['Close'])
low_signal_ma = percentB_belowzero(short_df['Position_MA'], short_df['Long_MA']) 
high_signal_ma = percentB_aboveone(short_df['Position_MA'], short_df['Long_MA'])

make_plots(short_df, args.stock,  low_signal, high_signal, low_signal_ma, high_signal_ma, '30d', False)



