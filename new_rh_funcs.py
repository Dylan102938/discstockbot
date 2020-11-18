from pyrh import Robinhood
import json
import threading
import time
import datetime

INSTRUMENT_BASE = "https://robinhood.com/options/instruments/"
paper_portfolio = {}
default = {'amt':1, 'watch_price':None}

def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)
    
    return friday.strftime("%Y-%m-%d")


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


class Order:

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


    def __str__(self):
        return_str = 'Order Type: ' + self.command + '\n'
        return_str += 'Option Type: ' + self.order_type + '\n'
        return_str += 'Parameters: ' + str(self.parameters) + '\n'
        return_str += 'Started: ' + self.started + '\n'
        if self.fulfilled:
            return_str += 'Fulfilled: ' + self.ended + '\n'
        return_str += 'Profits per Share: ' + str(self.profits) + '\n'

        return return_str


    def get_curr_price(self):
        curr_price = self.client.get_quote(self.ticker)
        curr_price = float(curr_price['last_trade_price'])
        
        return curr_price
    

    def increase_position(self):
        curr_price = self.get_curr_price()
        
        options = self.client.get_options(self.ticker, nearest_friday(), self.order_type)
        option = None

        if self.order_type == 'call':
            for o in options:
                if 0 < float(o['strike_price']) - curr_price < 0.5:
                    option = o
                    break
        else:
            for o in options:
                if 0 < curr_price - float(o['strike_price'])  < 0.5:
                    option = o
                    break

        return self.order_or_watch(option)


    def reduce_position(self, pct):
        # amt = self.client.get_positions(self.ticker, self.order_type)
        if 'breakeven' not in self.parameters and 'rest' not in self.parameters:
            try:
                paper_portfolio[self.ticker][self.order_type]['amt'] *= pct
                self.profits = self.get_curr_price() - paper_portfolio[self.ticker][self.order_type]['avg_cost']
                if paper_portfolio[self.ticker][self.order_type]['amt'] == 0:
                    paper_portfolio[self.ticker][self.order_type]['avg_cost'] = 0

                self.fulfilled = True
                self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

                return self
            
            except:
                return self

        else:
            self.pct = pct
            option = ''
            action = threading.Thread(target=self.wait_for_price, args=(option,))
            action.start()
            
            return self
        

    def order_or_watch(self, option):
        if not self.parameters['watch_price']:
            self.update_portfolio(self.parameters['amt'])

            return self

        else:
            action = threading.Thread(target=self.wait_for_price, args=(option,))
            action.start()

            return self


    def wait_for_price(self, option):
        count = 0
        while not self.fulfilled and count < 3600:
            time.sleep(5)

            price = self.get_curr_price()
            cost = paper_portfolio[self.ticker][self.order_type]['avg_cost']
            
            if self.parameters['watch_price'] and price >= self.parameters['watch_price'] and self.order_type == 'call':
                self.update_portfolio(self.parameters['amt'])
            
            elif self.parameters['watch_price'] and price <= self.parameters['watch_price'] and self.order_type == 'put':
                self.update_portfolio(self.parameters['amt'])

            if price <= cost and 'breakeven' in self.parameters:
                paper_portfolio[self.ticker][self.order_type]['amt'] *= self.pct
                if paper_portfolio[self.ticker][self.order_type]['amt'] == 0:
                    paper_portfolio[self.ticker][self.order_type]['avg_cost'] = 0
                self.profits = price - cost

                self.fulfilled = True
                self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            if 'rest' in self.parameters and (self.order_type == 'trim' or self.order_type == 'close'):
                paper_portfolio[self.ticker][self.order_type]['amt'] = 0
                paper_portfolio[self.ticker][self.order_type]['watch_price'] = 0
                self.profits = price - cost

                self.fulfilled = True
                self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

            count += 1
    
    
    def update_portfolio(self, amt):
        try: 
            existing_amt = paper_portfolio[self.ticker][self.order_type]['amt']
            additional_amt = self.parameters['amt']
            existing_cost = paper_portfolio[self.ticker][self.order_type]['avg_cost']
            additional_cost = self.get_curr_price()
            
            new_amt = existing_amt + additional_amt
            new_avg_cost = (existing_amt*existing_cost + additional_amt*additional_cost)/new_amt

            paper_portfolio[self.ticker][self.order_type]['amt'] = new_amt
            paper_portfolio[self.ticker][self.order_type]['avg_cost'] = new_avg_cost
            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        except:
            paper_portfolio[self.ticker] = {'call': {'amt':0, 'avg_cost':0}, 'put': {'amt':0, 'avg_cost':0}}

            paper_portfolio[self.ticker][self.order_type]['amt'] = self.parameters['amt']
            paper_portfolio[self.ticker][self.order_type]['avg_cost'] = self.get_curr_price()
            self.fulfilled = True
            self.ended = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    
    def watch(self):
        self.fulfilled = True
        self.ended = self.datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        return self


    def falsesafe(self):
        return self
    
    
    def get_object(self):
        return_dict = {
            'order_type': self.command,
            'option_type': self.order_type,
            'parameters': self.parameters,
            'started': self.started,
        }

        if self.fulfilled:
            return_dict['fulfilled'] = self.ended
            return_dict['profits_share'] = self.profits

        return return_dict


    order_dict = {
        'in': increase_position,
        'trim': lambda self: self.reduce_position(0.5),
        'watch': watch,
        'close': lambda self: self.reduce_position(0),
        'falsesafe': falsesafe
    }


