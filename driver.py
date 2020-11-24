import discord
from new_rh_funcs import *
import parser
import json

last_ticker = ""
last_category = ""
order_catalog = []
trades_json = {'paper_portfolio': paper_portfolio, 'order_catalog': order_catalog}
rh = Robinhood()

client = discord.Client()

@client.event
async def on_ready():
    print('Logged into {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    else:
        print('Message received:', message.content)
        return process_and_run(message.content)


def process_and_run(message):
    global last_ticker, last_category
    commands, cats, tickers, parameters = parser.words_driver()
    parsed_dict = parser.parse(message, commands, cats, tickers, parameters)

    if parsed_dict:
        print(parsed_dict)
        if not parsed_dict['ticker']:
            parsed_dict['ticker'] = last_ticker
        if not parsed_dict['category']:
            parsed_dict['category'] = last_ticker

        new_order = Order(rh, parsed_dict['command'], parsed_dict['ticker'], parsed_dict['category'], parse_params(parsed_dict['parameters']))
        if new_order:
            order_catalog.append(new_order)
            print(new_order)

            last_ticker = parsed_dict['ticker']
            last_category = parsed_dict['category']

            trades_json['paper_portfolio'] = paper_portfolio
            trades_json['order_catalog'] = order_catalog

            with open('paper_log.json', 'w') as f:
                json.dump(trades_json, f)

            return str(new_order)
        return 'Order Failed!'


# login to Robinhood
user = input("Enter Robinhood Email: ")
passw = input("Enter Robinhood Password: ")
rh.login(username=user, password=passw, challenge_type='sms')

# login to discord
disc_token = 'Nzc0NTIzNzMzODc2MDE1MTQ0.X6ZBcA.3Q7Mq-mgWRB4tKmjc5rIBwxtRVM'
client.run(disc_token)

