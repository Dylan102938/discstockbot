import random
import requests
import datetime

def generate_device_token():
    rands = []
    for i in range(0, 16):
        r = random.random()
        rand = 4294967296.0 * r
        rands.append((int(rand) >> ((3 & i) << 3)) & 255)

    hexa = []
    for i in range(0, 256):
        hexa.append(str(hex(i + 256)).lstrip("0x").rstrip("L")[1:])

    id = ""
    for i in range(0, 16):
        id += hexa[rands[i]]

        if (i == 3) or (i == 5) or (i == 7) or (i == 9):
            id += "-"

    return id


def id_for_option(symbol, expirationDate, strike, optionType):
    symbol = symbol.upper()
    chain_id = id_for_instrument(symbol, chain=True)
    payload = {
        'chain_id': chain_id,
        'expiration_dates': expirationDate,
        'strike_price': strike,
        'type': optionType,
        'state': 'active'
    }
    url = 'https://api.robinhood.com/options/instruments/'
    data = [None]
    try:
        res = requests.get(url, params=payload)
        res.raise_for_status()
        data = res.json()
    except (requests.exceptions.HTTPError, AttributeError) as message:
        print(message)

    counter = 2
    nextData = data
    try:
        data = data['results']
    except KeyError as message:
        print("{0} is not a key in the dictionary".format(message))
        return([None])

    if nextData['next']:
        print('Found Additional pages.')
    while nextData['next']:
        try:
            res = requests.get(nextData['next'])
            res.raise_for_status()
            nextData = res.json()
        except:
            print('Additional pages exist but could not be loaded.')
            return(data)
        print('Loading page '+str(counter)+' ...')
        counter += 1
        for item in nextData['results']:
            data.append(item)

    listOfOptions = [item for item in data if item["expiration_date"] == expirationDate]
    if (len(listOfOptions) == 0):
        print('Getting the option ID failed. Perhaps the expiration date is wrong format, or the strike price is wrong.')
        return(None)

    return(listOfOptions[0]['id'])


def id_for_instrument(symbol, chain=False):
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return(None)

    url = 'https://api.robinhood.com/instruments/'

    payload = {'symbol': symbol}
    try:
        res = requests.get(url, params=payload)
        res.raise_for_status()
        data = res.json()
    except (requests.exceptions.HTTPError, AttributeError) as message:
        print(message)
        data = None

    try:
        data = data['results'][0]
    except KeyError as message:
        print("{0} is not a key in the dictionary".format(message))
        data = None
    except IndexError as message:
        data = None

    if data and chain:
        return(data['tradable_chain_id'])
    elif data and not chain:
        return(data['id'])
    else:
        return(data)


def nearest_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta((3-today.weekday())%7+1)

    return friday.strftime("%Y-%m-%d")
