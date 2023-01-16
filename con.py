from collections import defaultdict

import ccxt
import requests
import telegram

BOT_TOKEN = "텔레그램 토큰"
CHAT_ID = "텔레그램 채팅 ID"
BINGX_API_URL = "https://api.bingbon.com/api/coingecko/v1/derivatives/contracts"
BINGX_PERP_API_URL = "https://api-swap-rest.bingbon.pro/api/v1/market/getAllContracts"
BINGX_PERP_TICKER_API_URL="https://api-swap-rest.bingbon.pro/api/v1/market/getLatestPrice?symbol="
GAP = 0.02

BN = ccxt.binanceusdm()
BingX = requests.get(BINGX_API_URL)

pairs = defaultdict(dict)
bing_data = BingX.json()["result"]
for data in bing_data:
    symbol = f"{data['base_currency']}"
    pairs[symbol]["bing"] = float(data["last_price"])

BINGX_PERP = [x["name"] for x in requests.get("https://api-swap-rest.bingbon.pro/api/v1/market/getAllContracts").json()["data"]["contracts"]]#이

for data in BINGX_PERP:
    res = requests.get(BINGX_PERP_TICKER_API_URL + f"{data}-USDT").json()
    pairs[data]["bing"] = float(res["data"]["tradePrice"])

bn_symbol_list =  [f"{symbol}/USDT" for symbol in pairs if f"{symbol}/USDT" in BN.load_markets() and f"{symbol}/USDT"]

binance_data = BN.fetch_tickers(bn_symbol_list)
for symbol, data in binance_data.items():
    symbol = symbol.replace("/USDT", "")
    pairs[symbol]["bn"] = float(data["info"]["lastPrice"])

bn_gap_list = dict()
for ticker, price in pairs.items():
    if "bn" in price:
        div_price = max(price["bing"], price["bn"]) / min(price["bing"], price["bn"])

        if GAP <= div_price - 1:
            price["bn_gap"] = f"{round(div_price - 1, 2)}%"
            bn_gap_list[ticker] = price

if bn_gap_list:
    bot = telegram.Bot(token=BOT_TOKEN)
    text = "빙 선선 갭 알림\n\n"
    if bn_gap_list:
        for ticker, price in bn_gap_list.items():
            text += f"{ticker} - GAP : {price['bn_gap']} / Binance : {price['bn']} - Bing : {price['bing']}\n"
        text += "\n"

    bot.sendMessage(chat_id=CHAT_ID, text=text)