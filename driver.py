import discord
import rh_funcs
import parser

token = 'Nzc0NTIzNzMzODc2MDE1MTQ0.X6ZBcA.rx_Z_W95iUD6OHOwu6YizIdvvtU'
USER = ""
PASS = ""

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
    commands, cats, tickers, parameters = parser.words_driver()
    parsed_dict = parser.parse(message, commands, cats, tickers, parameters)
    
    print("Parsed info:", parsed_dict)

    if parsed_dict:
        try:
            correct_func = rh_funcs.func_map[parsed_dict['command']][parsed_dict['category']]
            amt, watch_price = rh_funcs.parse_params(parsed_dict['parameters'])
            
            return correct_func(rh, parsed_dict['ticker'], amt, watch_price)
        
        except:
            return None


# login to robinhood
rh = Robinhood()
rh.login(username=USER, password=PASS, challenge_type='sms')            

# login to discord
client.run(token)

