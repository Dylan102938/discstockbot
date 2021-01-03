from rh import *

class Handler:
    def __init__(self):
        self.db, self.cursor = database.connect_db()
        self.cursor.execute("SELECT * FROM accounts;")
        self.accounts = self.cursor.fetchall()

    def execute_order(self, command, ticker, strike_price, option_type, price, exp_date, pct):
        order_datas = []
        for account in self.accounts:
            rh = Robinhood()
            rh.login(oauth=account[2], equity=1000)
            data = None

            try:
                ticker = ticker.upper().strip()
            except AttributeError as message:
                print(message)
                return None

            if command == 'in':
                amt = (pct*rh.equity)//(price*100)
                data = rh.place_buy(ticker, exp_date, strike_price, option_type, price, amt)

            elif command == 'close' or command == 'trim':
                position = rh.get_positions(target={'ticker': ticker, 'option_type': option_type})
                expiration_date = position['legs'][0]['expiration_date']
                amt = int(pct*float(position['quantity']))
                data = rh.place_sell(ticker, expiration_date, strike_price, option_type, price, amt)

            else:
                data = {'created_at': None}

            print(data)
            order_datas.append(data)

        return order_datas
