from uuid import uuid4
import json
import threading
import time
import datetime
import urllib.parse
import requests

INSTRUMENT_BASE = "https://robinhood.com/options/instruments/"
paper_portfolio = {}
default = {'amt': 1, 'watch_price': None}


# Returns nearest Friday, used to get next closest option
def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((3-today.weekday())%7+1)

    return friday.strftime("%Y-%m-%d")


# Changes dictionary or array to properly labeled dictionary
def parse_params(parameters):
    return_dict = dict(default)

    for param in parameters:
        if 'over' in param or 'below' in param:
            return_dict['watch_price'] = float(param.split()[1])
        if 'light' in param:
            return_dict['amt'] = 0.2
        if 'breakeven' in param:
            return_dict['breakeven'] = True
        if 'rest' in param:
            return_dict['rest'] = True

    return return_dict


# Order Class
class Order:
    """
    client: Robinhood client
    command: in, trim, watch, close, falsesafe
    ticker: stock ticker for order
    order_type: call, put
    parameters: additional order modifications as a dict
    """
    # [COMPLETE]
    def __init__(self, client, command, ticker, order_type, max_equity=1000, parameters={'amt':1, 'watch_price':None}):
        self.client = client
        self.command = command
        self.ticker = ticker
        self.order_type = order_type
        self.max_equity = max_equity
        self.parameters = parameters
        self.fulfilled = False
        self.profits = 0
        self.started = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        self.order_dict[command](self)

    # Returns stock info as string [COMPLETE]
    def __str__(self):
        return_str = 'Order Type: ' + self.command + '\n'
        return_str += 'Option Type: ' + self.order_type + '\n'
        return_str += 'Parameters: ' + str(self.parameters) + '\n'
        return_str += 'Started: ' + self.started + '\n'
        if self.fulfilled:
            return_str += 'Fulfilled: ' + self.ended + '\n'
        return_str += 'Profits per Share: ' + str(self.profits) + '\n'

        return return_str

    # object repr of order [COMPLETE]
    def get_object(self):
        return_dict = {
            'order_type': self.command,
            'ticker': self.ticker,
            'option_type': self.order_type,
            'parameters': self.parameters,
            'started': self.started,
        }

        if self.fulfilled:
            return_dict['fulfilled'] = self.ended
            return_dict['profits_per_share'] = self.profits

        return return_dict

    # handles 'in' command [COMPLETE]
    def increase_position(self):
        # no limit for strike price set
        if not self.parameters['watch_price']:
            self.place_buy()

            return self

        # limit for strike price set, start threading function
        else:
            action = threading.Thread(target=self.wait_for_price, args=())
            action.start()

            return self

    # Function handles 'trim' and 'close' command [COMPLETE]
    def reduce_position(self, pct):
        # no additional exiting parameters, exit position right away
        target = self.get_option_from_positions()
        if 'breakeven' not in self.parameters and 'rest' not in self.parameters:
            if target:
                self.place_sell(target, pct)

            return self

        # additional exiting parameters, pass to threading function
        else:
            action = threading.Thread(target=self.wait_for_price, args=(target, pct,))
            action.start()

            return self

    # function to handle watch command [COMPLETE]
    def watch(self):
        self.fulfilled = True
        self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        return self

    # function to handle falsesafe command [COMPELTE]
    def falsesafe(self):
        return self

    # threading function target [COMPLETE]
    def wait_for_price(self, target=None, pct=None):
        # check if item exists in portfolio
        try:
            cost = float(target['average_open_price'])
        except:
            cost = 0

        count = 0
        # checks if parameters match every 5 seconds, loops 3600 times total [COMPLETE]
        while not self.fulfilled and count < 3600:
            time.sleep(5)
            stock_price = self.get_curr_price()
            try:
                option_price = self.get_curr_option_price(option=self.get_option(link=target['legs'][0]['option']))
            except:
                option_price = None

            # check if watch price for call is satisfied
            if self.parameters['watch_price'] and stock_price >= self.parameters['watch_price'] and self.order_type == 'call':
                self.place_buy()

            # check if watch price for put is satisfied
            elif self.parameters['watch_price'] and stock_price <= self.parameters['watch_price'] and self.order_type == 'put':
                self.place_buy()

            # check if rest for close or trim is satisfied
            if 'rest' in self.parameters and (self.command == 'trim' or self.command == 'close'):
                if 'breakeven' in self.parameters:
                    pct = 0
                else:
                    self.place_sell(target, 0)

            # check if breakeven for close or trim order is satisfied
            if 'breakeven' in self.parameters and option_price <= cost:
                self.place_sell(target, pct)

            count += 1

    # gets current price of STOCK [COMPLETE]
    def get_curr_price(self):
        curr_price = self.client.get_quote(self.ticker)
        curr_price = float(curr_price['last_trade_price'])

        return curr_price

    # get option based on passed in parameters [COMPLETE]
    def get_option(self, link=''):
        if link:
            return {'url': link}

        curr_price = self.get_curr_price()

        options = self.client.get_options(self.ticker, nearest_friday(), self.order_type)
        option = None
        closest_price = None

        if self.order_type == 'call':
            for o in options:
                if float(o['strike_price']) - curr_price > 0:
                    if not option:
                        option = o
                        closest_price = float(o['strike_price'])
                    elif float(o['strike_price']) < closest_price:
                        option = o
                        closest_price = float(o['strike_price'])

        else:
            for o in options:
                if float(o['strike_price']) - curr_price < 0:
                    if not option:
                        option = o
                        closest_price = float(o['strike_price'])
                    elif float(o['strike_price']) > closest_price:
                        option = o
                        closest_price = float(o['strike_price'])
        return option

    # gets current price of OPTION [COMPLETE]
    def get_curr_option_price(self, option=None):
        if not option:
            option = self.get_option()
        instrument_url = urllib.parse.quote_plus(option['url'])

        # Custom request (pyrh is faulty)
        url = 'https://api.robinhood.com/marketdata/options/?instruments=' + instrument_url
        headers = dict(self.client.headers)
        headers['Authorization'] = 'Bearer ' + self.client.auth_token
        instr_data = json.loads(requests.get(url, headers=headers).text)

        price = float(instr_data['results'][0]['adjusted_mark_price']) * 100
        return price

    # gets current options positions
    def get_owned_options(self):
        url = 'https://api.robinhood.com/options/aggregate_positions/?nonzero=True'
        headers = {
            'authorization': 'Bearer ' + self.client.auth_token,
            'user-agent': 'Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)'
        }
        result = requests.get(url, headers=headers)
        result = json.loads(result.text)['results']
        option_list = []
        for option in result:
            if len(option['legs']) < 2:
                option_list.append(option)

        return option_list

    # finds an option given Order parameters from current positions:
    def get_option_from_positions(self):
        options = self.get_owned_options()

        found_option = None
        for o in options:
            if self.ticker == o['symbol'] and self.order_type == o['legs'][0]['option_type']:
                found_option = o
                break

        return found_option

    # calls buy endpoint on RH
    def place_buy(self):
        option = self.get_option()
        price = self.get_curr_option_price(option=option)
        actual_price = 0
        while actual_price < price:
            actual_price += 5
        price = actual_price
        amt = str(int(self.parameters['amt'] * self.max_equity / price))
        price = str(round(price / 100, 2))

        url = "https://api.robinhood.com/options/orders/"
        payload = "{\n" \
                  "    \"quantity\":\"" + amt + "\",\n" \
                  "    \"direction\":\"debit\",\n" \
                  "    \"price\":\"" + price + "\",\n" \
                  "    \"type\":\"limit\",\n" \
                  "    \"account\":\"https://api.robinhood.com/accounts/5QT80700/\",\n" \
                  "    \"time_in_force\":\"gfd\",\n" \
                  "    \"trigger\":\"immediate\",\n" \
                  "    \"legs\":[\n" \
                  "        {\n" \
                  "            \"side\":\"buy\",\n" \
                  "            \"option\":\"" + option['url'] + "\",\n" \
                  "            \"position_effect\":\"open\",\n" \
                  "            \"ratio_quantity\":\"1\"\n" \
                  "        }\n" \
                  "    ],\n" \
                  "    \"override_day_trade_checks\":false,\n" \
                  "    \"override_dtbp_checks\":false,\n" \
                  "    \"ref_id\":\"" + str(uuid4()) + "\"\n" \
                  "}"
        headers = {
            'x-robinhood-api-version': '1.411.9',
            'Authorization': 'Bearer ' + self.client.auth_token,
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 201:
            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            return json.loads(response.text)
        else:
            print("Request not successful: " + response.text)

    # calls sell endpoint on RH
    def place_sell(self, target, pct):
        price = self.get_curr_option_price(option=self.get_option(link=target['legs'][0]['option']))
        price = round(price / 5) * 5
        price = str(round(price / 100, 2))
        amt = str(int((1-pct)*float(target['quantity'])))

        url = "https://api.robinhood.com/options/orders/"
        payload = "{\n" \
                  "    \"quantity\":\"" + amt + "\",\n" \
                  "    \"direction\":\"credit\",\n" \
                  "    \"price\":\"" + price + "\",\n" \
                  "    \"type\":\"limit\",\n" \
                  "    \"account\":\"https://api.robinhood.com/accounts/5QT80700/\",\n" \
                  "    \"time_in_force\":\"gfd\",\n" \
                  "    \"trigger\":\"immediate\",\n" \
                  "    \"legs\":[\n" \
                  "        {\n" \
                  "            \"side\":\"sell\",\n" \
                  "            \"option\":\"" + target['legs'][0]['option'] + "\",\n" \
                  "            \"position_effect\":\"close\",\n" \
                  "            \"ratio_quantity\":\"" + str(target['legs'][0]['ratio_quantity']) + "\"\n" \
                  "        }\n" \
                  "    ],\n" \
                  "    \"override_day_trade_checks\":false,\n" \
                  "    \"override_dtbp_checks\":false,\n" \
                  "    \"ref_id\":\"" + str(uuid4()) + "\"\n" \
                  "}"
        headers = {
            'x-robinhood-api-version': '1.411.9',
            'Authorization': 'Bearer ' + self.client.auth_token,
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 201:
            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            return json.loads(response.text)
        else:
            print("Request not successful: " + response.text)

    # function map [COMPLETE]
    order_dict = {
        'in': increase_position,
        'trim': lambda self: self.reduce_position(0.5),
        'watch': watch,
        'close': lambda self: self.reduce_position(0),
        'falsesafe': falsesafe
    }
