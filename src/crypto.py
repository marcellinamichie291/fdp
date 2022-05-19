import pandas as pd
import ccxt
import time
from datetime import datetime
from . import utils

'''
format for since : dd_mm_yyyy
'''
def _get_ohlcv(exchange, symbol, start, end=None, timeframe="1d", limit=None):
    if exchange == None or symbol == None or start == None:
        return None

    since = int(datetime.strptime(start, "%d_%m_%Y").timestamp())*1000
    if end != None:
        start = datetime.strptime(start, '%d_%m_%Y')
        end = datetime.strptime(end, '%d_%m_%Y')
        delta = end - start
        limit  = delta.days # days
        if timeframe == "1m":
            limit = limit * 24 * 60
        elif timeframe == "1h":
            limit = limit * 24

    df = pd.DataFrame(exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since, limit=limit))
    df = df.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
    df = df.set_index(df['timestamp'])
    df.index = pd.to_datetime(df.index, unit='ms')
    del df['timestamp']
    return df

def _custom_filter(symbol):
    return (symbol[-4:] in ["/EUR", "/USD"] or symbol[-5:] in ["/EURS"]) and ("BTC" in symbol or "ETH" in symbol or "BNB" in symbol)

def _get_exchange(exchange_market):
    exchange = None
    if exchange_market == "hitbtc":
        exchange = ccxt.hitbtc()
    elif exchange_market == "bitmex":
        exchange = ccxt.bitmex()
    elif exchange_market == "binance":
        exchange = ccxt.binance()
    elif exchange_market == "ftx":
        exchange = ccxt.ftx()
    return exchange

def get_exchange_and_markets(exchange_name):
    exchange = _get_exchange(exchange_name)
    if exchange == None:
        return None, {}

    markets = exchange.load_markets()
    return exchange, markets

def get_list_symbols(exchange_name):
    exchange, markets = get_exchange_and_markets(exchange_name)
    if bool(exchange) == False:
        return []

    symbols = exchange.symbols
    symbols = list(filter(_custom_filter, symbols))

    return symbols

def get_dataframe_symbols(exchange):
    symbols = get_list_symbols(exchange)
    n = len(symbols)
    df = utils.make_df_stock_info(symbols, [''] * n, [''] * n, [''] * n, [''] * n, [''] * n, [''] * n)

    return df

def get_list_symbols_hitbtc():
    return get_list_symbols("hitbtc")

def get_list_symbols_bitmex():
    return get_list_symbols("bitmex")

def get_list_symbols_binance():
    return get_list_symbols("binance")

def get_list_symbols_ftx():
    return get_list_symbols("ftx")

def get_symbol_ticker(exchange_market, symbol):
    exchange = _get_exchange(exchange_market)
    if exchange == None:
        return []

    exchange.load_markets()
    if symbol not in exchange.symbols:
        return {}

    ticker = exchange.fetch_ticker(symbol)
    return ticker

def get_symbol_ohlcv(exchange_name, symbol, start=None, end=None, timeframe="1d", length=None):
    # manage some errors
    if exchange_name == "hitbtc" and length > 1000:
        return "for hitbtc, length must be in [1, 1000]"

    exchange = _get_exchange(exchange_name)
    if exchange == None:
        return "exchange not found"

    exchange.load_markets()
    if symbol not in exchange.symbols or exchange.has['fetchOHLCV'] == False:
        return "symbol not found"

    ohlcv = _get_ohlcv(exchange, symbol, start, end, timeframe, length)
    return ohlcv

def apply_filter_on_symbol_with_volume_gt_threshold(symbols, markets, threshold):
    return [symbol for symbol in symbols if float(markets[symbol]['info']['quoteVolume24h']) > threshold]

def apply_filter_on_symbol_with_name_ending_with(symbols, end):
    return [symbol for symbol in symbols if (symbol[-len(end):] == end and "BULL" not in symbol and "HALF" not in symbol and "EDGE" not in symbol and "BEAR" not in symbol)]


###
### gainers
###
def _get_top_gainers_for_change(symbols, markets, change, n):
    df = pd.DataFrame(symbols, columns=['symbol'])
    df['symbol'] = df['symbol'].astype("string")
    df = df.set_index('symbol', drop=False)
    symbols = df['symbol'].to_list()

    for symbol in symbols:
        df.loc[symbol, change] = float(markets[symbol]['info'][change]) * 100

    df.sort_values(by=[change], ascending=False, inplace=True)
    df.reset_index(inplace=True, drop=True)
    df['rank_'+change] = df.index
    df = df.head(n)
    return df

def get_top_gainers(exchange_name, n):
    exchange, markets = get_exchange_and_markets(exchange_name)
    symbols = exchange.symbols

    # filters on symbols
    symbols = apply_filter_on_symbol_with_name_ending_with(symbols, '/USD')
    symbols = apply_filter_on_symbol_with_volume_gt_threshold(symbols, markets, 10000)

    # get the gainers
    gainers1h = _get_top_gainers_for_change(symbols, markets, "change1h", n)
    gainers24h = _get_top_gainers_for_change(symbols, markets, "change24h", n)

    # merge
    df = pd.merge(gainers1h, gainers24h)

    return df
