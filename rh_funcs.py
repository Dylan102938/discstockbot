from pyrh import Robinhood
import json
import threading
import time
import datetime
import urllib.parse
import requests

INSTRUMENT_BASE = "https://robinhood.com/options/instruments/"
paper_portfolio = {}
default = {'amt':1, 'watch_price':None}


# Returns nearest Friday, used to get next closest option
def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((3-today.weekday())%7+1)
    
    return friday.strftime("%Y-%m-%d")


# Changes dictionary or array to properly labeled dictionary
def parse_params(parameters):
    return_dict = dict(default)

    for param in parameters:
        if 'above' in param or 'below' in param:
            return_dict['watch_price'] = float(param.split()[1])
        if 'light' in param:
            return_dict['amt'] = 0.15
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
    def __init__(self, client, command, ticker, order_type, parameters={'amt':1, 'watch_price':None}):
        self.client = client
        self.command = command
        self.ticker = ticker
        self.order_type = order_type
        self.parameters = parameters
        self.fulfilled = False
        self.profits = 0
        self.started = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        self.order_dict[command](self)

    # Returns stock info as string
    def __str__(self):
        return_str = 'Order Type: ' + self.command + '\n'
        return_str += 'Option Type: ' + self.order_type + '\n'
        return_str += 'Parameters: ' + str(self.parameters) + '\n'
        return_str += 'Started: ' + self.started + '\n'
        if self.fulfilled:
            return_str += 'Fulfilled: ' + self.ended + '\n'
        return_str += 'Profits per Share: ' + str(self.profits) + '\n'

        return return_str

    # gets current price of STOCK
    def get_curr_price(self):
        curr_price = self.client.get_quote(self.ticker)
        curr_price = float(curr_price['last_trade_price'])
        
        return curr_price

    # gets current price of OPTION
    def get_curr_option_price(self, option=None):
        if not option:
            option = self.get_option()
        instrument_url = urllib.parse.quote_plus(option['url'])

        # Custom request (pyrh is faulty)
        url = 'https://api.robinhood.com/marketdata/options/?instruments=' + instrument_url
        headers = dict(self.client.headers)
        headers['Authorization'] = 'Bearer ' + self.client.auth_token
        instr_data = json.loads(requests.get(url, headers=headers).text)

        price = float(instr_data['results'][0]['ask_price'])*100
        return price

    # handles 'in' command
    def increase_position(self):
        # get option of interest
        option = self.get_option()

        # no limit for strike price set
        if not self.parameters['watch_price']:
            self.update_portfolio()
            return self

        # limit for strike price set, start threading function
        else:
            action = threading.Thread(target=self.wait_for_price, args=())
            action.start()

            return self

    # Function handles 'trim' and 'close' command
    def reduce_position(self, pct):
        # no additional exiting parameters, exit position right away
        if 'breakeven' not in self.parameters and 'rest' not in self.parameters:
            # replace with actual selling function
            paper_portfolio[self.ticker][self.order_type]['amt'] *= pct

            o = self.get_option(link=paper_portfolio[self.ticker][self.order_type]['link'])
            self.profits = self.get_curr_option_price(option=o) - paper_portfolio[self.ticker][self.order_type]['avg_cost']
            
            if paper_portfolio[self.ticker][self.order_type]['amt'] == 0:
                paper_portfolio[self.ticker][self.order_type]['avg_cost'] = 0

            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            return self

        # additional exiting parameters, pass to threading function
        else:
            self.pct = pct
            action = threading.Thread(target=self.wait_for_price, args=())
            action.start()
            
            return self

    # function to handle watch command
    def watch(self):
        self.fulfilled = True
        self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        return self

    # function to handle falsesafe command
    def falsesafe(self):
        return self

    # threading function target
    def wait_for_price(self):
        count = 0

        # checks if parameters match every 5 seconds, loops 3600 times total
        while not self.fulfilled and count < 3600:
            time.sleep(5)

            price = self.get_curr_price)

            # check if item exists in portfolio dict
            try:
                cost = paper_portfolio[self.ticker][self.order_type]['avg_cost']
            except:
                cost = 0

            # check if watch price fpr call is satisfied
            if self.parameters['watch_price'] and price >= self.parameters['watch_price'] and self.order_type == 'call':
                self.update_portfolio()

            # check if watch price for put is satisfied
            elif self.parameters['watch_price'] and price <= self.parameters['watch_price'] and self.order_type == 'put':
                self.update_portfolio()

            # check if breakeven for close or trim order is satisfied
            if price <= cost and 'breakeven' in self.parameters:
                # replace with actual selling function
                paper_portfolio[self.ticker][self.order_type]['amt'] *= self.pct
                
                o = self.get_option(link=paper_portfolio[self.ticker][self.order_type]['link'])
                self.profits = self.get_curr_option_price(option=o) - cost
                
                if paper_portfolio[self.ticker][self.order_type]['amt'] == 0:
                    paper_portfolio[self.ticker][self.order_type]['avg_cost'] = 0

                self.fulfilled = True
                self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            # check if rest for close or trim is satisfied
            if 'rest' in self.parameters and (self.command == 'trim' or self.command == 'close'):
                paper_portfolio[self.ticker][self.order_type]['amt'] = 0
                
                o = self.get_option(link=paper_portfolio[self.ticker][self.order_type]['link'])
                self.profits = self.get_curr_option_price(option=o) - cost

                paper_portfolio[self.ticker][self.order_type]['avg_cost'] = 0

                self.fulfilled = True
                self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            count += 1

    # function to add stocks to portfolio after purchasing call, put
    def update_portfolio(self):
        try: 
            existing_amt = paper_portfolio[self.ticker][self.order_type]['amt']
            additional_amt = self.parameters['amt']
            existing_cost = paper_portfolio[self.ticker][self.order_type]['avg_cost']
            additional_cost = self.get_curr_option_price()
            
            new_amt = existing_amt + additional_amt
            new_avg_cost = (existing_amt*existing_cost + additional_amt*additional_cost)/new_amt

            paper_portfolio[self.ticker][self.order_type]['amt'] = new_amt
            paper_portfolio[self.ticker][self.order_type]['avg_cost'] = new_avg_cost

            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        except:
            paper_portfolio[self.ticker] = {'call': {'amt':0, 'avg_cost':0, 'link':''}, 'put': {'amt':0, 'avg_cost':0, 'link':''}}

            paper_portfolio[self.ticker][self.order_type]['amt'] = self.parameters['amt']
            paper_portfolio[self.ticker][self.order_type]['avg_cost'] = self.get_curr_option_price()
            paper_portfolio[self.ticker][self.order_type]['link'] = self.get_option()

            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # get option based on passed in parameters
    def get_option(self, link=''):
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
        
        if link:


        return option

    # object repr of order
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
            return_dict['profits_share'] = self.profits

        return return_dict

    # function map
    order_dict = {
        'in': increase_position,
        'trim': lambda self: self.reduce_position(0.5),
        'watch': watch,
        'close': lambda self: self.reduce_position(0),
        'falsesafe': falsesafe
    }
