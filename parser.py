commands_file = 'keywords/commands.txt'
categories_file = 'keywords/cats.txt'
parameters_file = 'keywords/parameters.txt'
ticker_file = 'keywords/tickers.txt'


def parse(sent, commands, cats, tickers, parameters):
    command, cat, ticker, params = "", "", "", []
    s = sent.split()

    for word in s:
        if word.lower() in commands:
            command = eval(commands[word.lower()])
        
        if word.lower() in cats:
            cat = cats[word.lower()]

        if word.lower() in tickers:
            ticker = tickers[word.lower()]
    
    if command != "":
        for i in range(len(s)):
            if s[i-1].lower() in parameters:
                params.append(eval(parameters[s[i - 1].lower()]))

        if "%+" in sent or "%+" in sent:
            params = ['fake']

        return {'command': command, 'ticker': ticker, 'category': cat, 'parameters': params}


def load_words(name):
    words = dict()

    with open(name, 'r') as f:
        word = f.readline()
        while word:
            label, word = word.strip().split(', ')
            words[label] = word

            word = f.readline()

    return words


def words_driver():
    return load_words(commands_file), \
           load_words(categories_file), \
           load_words(ticker_file), \
           load_words(parameters_file)

