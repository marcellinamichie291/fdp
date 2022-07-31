import pandas as pd
from parse import parse
from stockstats import StockDataFrame as Sdf
from finta import TA
import numpy as np


class SuperTrend():
    def __init__(
        self,
        high,
        low,
        close,
        atr_window=10,
        atr_multi=3
    ):
        self.high = high
        self.low = low
        self.close = close
        self.atr_window = atr_window
        self.atr_multi = atr_multi
        self._run()
        
    def _run(self):
        # calculate ATR
        price_diffs = [self.high - self.low, 
                    self.high - self.close.shift(), 
                    self.close.shift() - self.low]
        true_range = pd.concat(price_diffs, axis=1)
        true_range = true_range.abs().max(axis=1)
        # default ATR calculation in supertrend indicator
        atr = true_range.ewm(alpha=1/self.atr_window,min_periods=self.atr_window).mean() 
        # atr = ta.volatility.average_true_range(high, low, close, atr_period)
        # df['atr'] = df['tr'].rolling(atr_period).mean()
        
        # HL2 is simply the average of high and low prices
        hl2 = (self.high + self.low) / 2
        # upperband and lowerband calculation
        # notice that final bands are set to be equal to the respective bands
        final_upperband = upperband = hl2 + (self.atr_multi * atr)
        final_lowerband = lowerband = hl2 - (self.atr_multi * atr)
        
        # initialize Supertrend column to True
        supertrend = [True] * len(self.close)
        
        for i in range(1, len(self.close)):
            curr, prev = i, i-1
            
            # if current close price crosses above upperband
            if self.close[curr] > final_upperband[prev]:
                supertrend[curr] = True
            # if current close price crosses below lowerband
            elif self.close[curr] < final_lowerband[prev]:
                supertrend[curr] = False
            # else, the trend continues
            else:
                supertrend[curr] = supertrend[prev]
                
                # adjustment to the final bands
                if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                    final_lowerband[curr] = final_lowerband[prev]
                if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                    final_upperband[curr] = final_upperband[prev]

            # to remove bands according to the trend direction
            if supertrend[curr] == True:
                final_upperband[curr] = np.nan
            else:
                final_lowerband[curr] = np.nan
                
        self.st = pd.DataFrame({
            'Supertrend': supertrend,
            'Final Lowerband': final_lowerband,
            'Final Upperband': final_upperband
        })
        
    def super_trend_upper(self):
        return self.st['Final Upperband']
        
    def super_trend_lower(self):
        return self.st['Final Lowerband']
        
    def super_trend_direction(self):
        return self.st['Supertrend']



def compute_indicators(df, indicators, keep_only_requested_indicators = False):
    if not isinstance(df, pd.DataFrame):
        return df

    # call stockstats
    stock = Sdf.retype(df.copy())

    # compute the indicators
    columns = list(df.columns)
    for indicator in indicators:
        if indicator in columns:
            continue

        trend_parsed = parse('trend_{}d', indicator)
        sma_parsed = parse('sma_{}', indicator)
        ema_parsed = parse('ema_{}', indicator)
        wma_parsed = parse('wma_{}', indicator)

        if trend_parsed != None and trend_parsed[0].isdigit():
            seq = int(trend_parsed[0])
            diff = df["close"] - df["close"].shift(seq)
            df["trend_"+str(seq)+"d"] = diff.gt(0).map({False: 0, True: 1})

        elif sma_parsed != None and sma_parsed[0].isdigit():
            seq = int(sma_parsed[0])
            df["sma_"+str(seq)] = TA.SMA(stock, seq).copy()

        elif ema_parsed != None and ema_parsed[0].isdigit():
            period = int(ema_parsed[0])
            df["ema_"+str(period)] = TA.EMA(stock, period = period).copy()

        elif wma_parsed != None and wma_parsed[0].isdigit():
            period = int(wma_parsed[0])
            df["wma_"+str(period)] = TA.WMA(stock, period = period).copy()

        elif indicator == 'macd':
            df['macd'] = stock.get('macd').copy() # from stockstats
            #df['macd'] = TA.MACD(stock)['MACD'].copy() # from finta

        elif indicator == 'macds':
            df['macds'] = stock.get('macds').copy() # from stockstats

        elif indicator == 'macdh':
            df['macdh'] = stock.get('macdh').copy() # from stockstats

        elif indicator == 'bbands':
            bbands = TA.BBANDS(stock).copy()
            df = pd.concat([df, bbands], axis = 1)
            df.rename(columns={'BB_UPPER': 'bb_upper'}, inplace=True)
            df.rename(columns={'BB_MIDDLE': 'bb_middle'}, inplace=True)
            df.rename(columns={'BB_LOWER': 'bb_lower'}, inplace=True)

        elif indicator == 'rsi_30':
            df['rsi_30'] = stock.get('rsi_30').copy()
        
        elif indicator == 'cci_30':
            df['cci_30'] = stock.get('cci_30').copy()
        
        elif indicator == 'dx_30':
            df['dx_30'] = stock.get('dx_30').copy()
        
        elif indicator == 'williams_%r':
            df['williams_%r'] = TA.WILLIAMS(stock).copy()

        elif indicator == 'stoch_%k':
            df['stoch_%k'] = TA.STOCH(stock).copy()

        elif indicator == 'stoch_%d':
            df['stoch_%d'] = TA.STOCHD(stock).copy()
           
        elif indicator == 'er':
            df['er'] = TA.ER(stock).copy()
           
        elif indicator == 'stc':
            df['stc'] = TA.STC(stock).copy()
           
        elif indicator == 'atr':
            df['atr'] = TA.ATR(stock).copy()
           
        elif indicator == 'adx':
            df['adx'] = TA.ADX(stock).copy()
           
        elif indicator == 'roc':
            df['roc'] = TA.ROC(stock).copy()

        elif indicator == 'mom':
            df['mom'] = TA.MOM(stock).copy()

        elif indicator == 'simple_rtn':
            df['simple_rtn'] = df['close'].pct_change()

        elif indicator == "super_trend_direction":
            super_trend = SuperTrend(
                    df['high'], 
                    df['low'], 
                    df['close'], 
                    15, # self.st_short_atr_window
                    5 # self.st_short_atr_multiplier
                )
                
            df['super_trend_direction'] = super_trend.super_trend_direction()
            df['super_trend_direction'] = df['super_trend_direction'].shift(1)


    # keep only the requested indicators
    if keep_only_requested_indicators:
        for column in list(df.columns):
            if not column in indicators:
                df.drop(columns=[column], inplace=True)

    return df
    
def remove_features(df, features):
    for feature in features:
        try:
            df.drop(feature, axis=1, inplace=True)
        except KeyError as feature:
            print("{}. Columns are {}".format(feature, df.columns))
    return df

def normalize_column_headings(df):
    # Change all column headings to be lower case, and remove spacing
    df.columns = [str(x).lower().replace(' ', '_') for x in df.columns]
    return df

def get_trend_info(df):
    tmp = pd.concat([df['close']], axis=1, keys=['close'])
    tmp = compute_indicators(tmp, ["trend_1d"])
    tmp['shift_trend_1d'] = tmp['trend_1d'].shift(-1)
    tmp.dropna(inplace=True)

    tmp['true_positive'] = np.where((tmp['trend_1d'] == 1) & (tmp['shift_trend_1d'] == 1), 1, 0)
    tmp['true_negative'] = np.where((tmp['trend_1d'] == 0) & (tmp['shift_trend_1d'] == 0), 1, 0)
    tmp['false_positive'] = np.where((tmp['trend_1d'] == 1) & (tmp['shift_trend_1d'] == 0), 1, 0)
    tmp['false_negative'] = np.where((tmp['trend_1d'] == 0) & (tmp['shift_trend_1d'] == 1), 1, 0)

    # how many times the trend is up
    trend_counted = tmp['trend_1d'].value_counts(normalize=True)
    trend_ratio = 100 * trend_counted[1]

    # how many times trend today = trend tomorrow
    true_positive = 100*tmp['true_positive'].value_counts(normalize=True)[1]
    true_negative = 100*tmp['true_negative'].value_counts(normalize=True)[1]
    false_positive = 100*tmp['false_positive'].value_counts(normalize=True)[1]
    false_negative = 100*tmp['false_negative'].value_counts(normalize=True)[1]

    return trend_ratio, true_positive, true_negative, false_positive, false_negative

def get_stats_for_trend_up(df, n_forward_days):
    tmp = df.copy()

    indicator = "trend_"+str(n_forward_days)+"d"
    if indicator not in tmp.columns:
        tmp = compute_indicators(tmp, [indicator])

    # how many times the trend is up for d+n_forward_days
    trend_counted = tmp[indicator].value_counts(normalize=True)
    trend_ratio = 100 * trend_counted[1]

    return trend_ratio

def get_stats_on_trend_today_equals_trend_tomorrow(df):
    tmp = pd.concat([df['close']], axis=1, keys=['close'])
    tmp = compute_indicators(tmp, ["trend_1d"])
    tmp['shift_trend'] = tmp["trend_1d"].shift(-1)
    tmp.dropna(inplace=True)

    tmp['true_positive'] = np.where((tmp["trend_1d"] == 1) & (tmp['shift_trend'] == 1), 1, 0)
    tmp['true_negative'] = np.where((tmp["trend_1d"] == 0) & (tmp['shift_trend'] == 0), 1, 0)
    tmp['false_positive'] = np.where((tmp["trend_1d"] == 1) & (tmp['shift_trend'] == 0), 1, 0)
    tmp['false_negative'] = np.where((tmp["trend_1d"] == 0) & (tmp['shift_trend'] == 1), 1, 0)

    # how many times trend today = trend tomorrow
    true_positive = 100*tmp['true_positive'].value_counts(normalize=True)[1]
    true_negative = 100*tmp['true_negative'].value_counts(normalize=True)[1]
    false_positive = 100*tmp['false_positive'].value_counts(normalize=True)[1]
    false_negative = 100*tmp['false_negative'].value_counts(normalize=True)[1]

    return true_positive, true_negative, false_positive, false_negative
