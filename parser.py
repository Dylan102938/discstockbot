def parse(sent, commands="", cats="", tickers="", additional=""):
    action = ""
    cat = ""
    ticker = ""

    for word in sent.split():
        if word.lower() in commands:
            action = commands[word.lower()]
        
        if action == "" and word.lower() in ['call', 'calls', 'put', 'puts']:
            action = "in"
        
        if word.lower() in cats:
            cat = cats[word.lower()]

        if word.lower() in tickers:
            ticker = tickers[word.lower()]
    
    if action != "":
        parameters = []
        sent = sent.split()

        for i in range(1, len(sent)):
            if sent[i-1].lower() in additional:
                print(additional[sent[i-1].lower()])
                parameters.append(eval(additional[sent[i-1].lower()]))
        
        if sent[0].lower() in additional:
            try:
                parameters.append(eval(additional[sent[0].lower()]))
            except:
                pass
        
        if sent[len(sent)-1].lower() in additional:
            try:
                parameters.append(eval(additional[sent[len(sent)-1].lower()]))
            except:
                pass


        print(action, ticker, cat, parameters)


def load_words(name):
    words = dict()

    with open (name, 'r') as f:
        word = f.readline()
        while word:
            label, word = word.strip().split(', ')
            words[label] = word

            word = f.readline()

    return words


def words_driver():
    return load_words('commands.txt'), load_words('cats.txt'), load_words('tickers.txt'), load_words('parameters.txt')


commands, cats, tickers, parameters = words_driver()
with open('log.txt') as f:
    line = f.readline()
    while line:
        print(line.strip())
        parse(line, commands, cats, tickers, parameters)
        print()
        
        line = f.readline()

