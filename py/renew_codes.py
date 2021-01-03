from handler import *
import time

def main():
    while True:
        time.sleep(5)
        curr_time = time.time()

        h = Handler()
        for account in h.accounts:
            if float(account[3]) - curr_time < 3600:
                print(account[1] + "'s oauth token is about to expire!")
                rh = Robinhood()
                data=rh.refresh_oauth(account[2], account[4])
                
                print(data)

if __name__ == "__main__":
    main()
