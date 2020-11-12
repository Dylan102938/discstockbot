from pyrh import Robinhood
import json
import threading
import time
import datetime

INSTRUMENT_BASE = "https://robinhood.com/options/instruments/"


def in_call(client, ticker, amt=1, watch_price=None):
    curr_price = get_curr_price(client, ticker)

    options = client.get_options(ticker, nearest_friday(), 'call')
    option = None

    for o in options:
        if 0 < float(o['strike_price']) - curr_price < 0.5:
            option = o
            break

    return order_or_watch(client, ticker, option, amt, watch_price, watch_call)


def watch_call(client, ticker, option, amt, watch_price):
    curr_price = get_curr_price(client, ticker)

    counter = 0
    while curr_price < watch_price and counter < 3600:
        time.sleep(5)
        curr_price = get_curr_price(client, ticker)
        counter += 1

    instrument = INSTRUMENT_BASE + option['id']
    client.place_buy_order(instrument, amt)
    return True


def in_put(client, ticker, amt=1, watch_price=None):
    curr_price = get_curr_price(client, ticker)

    options = client.get_options(ticker, nearest_friday, 'put')
    option = None

    for o in options:
        if 0 < curr_price - float(o['strike_price']) < 0.5:
            option = o
            break

    return order_or_watch(client, ticker, option, amt, watch_price, watch_put)


def watch_put(client, ticker, option, amt, watch_price):
    curr_price = get_curr_price(client, ticker)

    counter = 0
    while curr_price > watch_price and counter < 3600:
        time.sleep(5)
        curr_price = get_curr_price(client, ticker)
        counter += 1

    instrument = INSTRUMENT_BASE + option['id']
    client.place_buy_order(instrument, amt)
    return True


def order_or_watch(client, ticker, option, amt, watch_price, watch_func):
    if not watch_price and option:
        # print(option)
        instrument = INSTRUMENT_BASE + option['id']
        client.place_buy_order(instrument, 1)
        return True

    elif watch_price and option:
        action = threading.Thread(target=watch_func, args=(client, ticker, option, amt, watch_price,))
        action.start()
        return True

    return False


def trim_position(client, ticker, pct=0.5, last_stock=""):
    positions = client.securities_owned()
    return positions['results']


def get_curr_price(client, ticker):
    curr_price = client.get_quote(ticker)
    curr_price = float(curr_price['last_trade_price'])
    return curr_price


def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    return friday.strftime("%Y-%m-%d")


def main():
    rh = Robinhood()
    rh.login(username="", password="", challenge_type="sms")
    print(json.dumps(trim_position(rh, 'AAPL'), indent=4))


if __name__ == "__main__":
    main()
