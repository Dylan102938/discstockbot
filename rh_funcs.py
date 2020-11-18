from pyrh import Robinhood
import json
import threading
import time
import datetime

INSTRUMENT_BASE = "https://robinhood.com/options/instruments/"


# Calls
def in_call(client, ticker, parameters={'amt':1, 'watch_price':None}):
    curr_price = get_curr_price(client, ticker)

    options = client.get_options(ticker, nearest_friday(), 'call')
    option = None

    for o in options:
        if 0 < float(o['strike_price']) - curr_price < 0.5:
            option = o
            break

    return order_or_watch(client, ticker, option, parameters, watch_call)


def watch_call(client, ticker, option, parameters):
    curr_price = get_curr_price(client, ticker)

    counter = 0
    while curr_price < parameters['watch_price'] and counter < 3600:
        time.sleep(5)
        curr_price = get_curr_price(client, ticker)
        counter += 1

    instrument = INSTRUMENT_BASE + option['id']
    client.place_buy_order(instrument, parameters['amt'])
    return True


# Puts
def in_put(client, ticker, parameters={'amt':1, 'watch_price':None}):
    curr_price = get_curr_price(client, ticker)

    options = client.get_options(ticker, nearest_friday(), 'put')
    option = None

    for o in options:
        if 0 < curr_price - float(o['strike_price']) < 0.5:
            option = o
            break

    return order_or_watch(client, ticker, option, parameters, watch_put)


def watch_put(client, ticker, option, parameters):
    curr_price = get_curr_price(client, ticker)

    counter = 0
    while curr_price > parameters['watch_price'] and counter < 3600:
        time.sleep(5)
        curr_price = get_curr_price(client, ticker)
        counter += 1

    instrument = INSTRUMENT_BASE + option['id']
    client.place_buy_order(instrument, parameters['amt'])
    return True


# Order or Watch Function
def order_or_watch(client, ticker, option, parameters, watch_func):
    if not parameters['watch_price'] and option:
        # print(option)
        instrument = INSTRUMENT_BASE + option['id']
        client.place_buy_order(instrument, parameters['amt'])
        return True

    elif parameters['watch_price'] and option:
        action = threading.Thread(target=watch_func, args=(client, ticker, option, parameters,))
        action.start()
        return True

    return False


# Selling/reducing position size
def reduce_position(client, ticker, last_stock="", parameters={'amt':1}):
    if not ticker:
        reduce(client, last_stock, parameters['amt'])

    else:
        reduce(client, ticker, parameters['amt'])

    return True


def reduce(client, ticker, amt):
    # client.sell_pos(...)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    curr_price = get_curr_price(client, ticker)

    return 'Sold ' + str(amt) + ' of ' + ticker + ' at ' + now + ' for ' + str(curr_price)



# Helper Functions
def get_curr_price(client, ticker):
    curr_price = client.get_quote(ticker)
    curr_price = float(curr_price['last_trade_price'])
    return curr_price


def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    return friday.strftime("%Y-%m-%d")



def parse_params(parameters):
    return_dict = dict()

    for param in parameters:
        if 'above' in param or 'below' in param:
            return_dict['watch_price'] = float(param.split()[1])
        if 'light' in param:
            return_dict['watch_price'] = 0.15
        if 'breakeven' in param:
            return_dict['breakeven'] = True
    
    return return_dict 


def main():
    rh = Robinhood()
    rh.login(username="", password="", challenge_type="sms")
    print(json.dumps(trim_position(rh, 'AAPL'), indent=4))


if __name__ == "__main__":
    main()
