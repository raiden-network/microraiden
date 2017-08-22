import json
from tkinter import ttk
import tkinter
import logging

from raiden_mps import Client, DefaultHTTPClient
from raiden_mps.config import (
    CHANNEL_MANAGER_ADDRESS,
    TEST_SENDER_PRIVKEY,
    TEST_RECEIVER_PRIVKEY,
)
from raiden_mps.proxy.content import PaywalledProxyUrl
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy


log = logging.getLogger(__name__)

def start_proxy():
    app = PaywalledProxy(
        CHANNEL_MANAGER_ADDRESS,
        TEST_RECEIVER_PRIVKEY,
        'eth_ticker_proxy.pkl'
    )
    app.add_content(PaywalledProxyUrl(
        "[A-Z]{6}",
        1,
        lambda request: 'api.kraken.com/0/public/Ticker?pair=' + request
    ))
    app.run(debug=True)
    return app


class Main(ttk.Frame):
    def __init__(self):
        self.root = tkinter.Tk()
        ttk.Frame.__init__(self, self.root)
        self.root.title('mRaiden ETH Ticker')
        self.pack()
        self.pricevar = tkinter.StringVar()
        ttk.Label(self, textvariable=self.pricevar, font=('Helvetica', '72')).pack()

        self.app = start_proxy()
        self.client = Client(TEST_SENDER_PRIVKEY)
        self.httpclient = DefaultHTTPClient(self.client, 'localhost', 5000)

    def run(self):
        self.root.after(0, self.query_price)
        self.root.mainloop()

    def query_price(self):
        response = self.httpclient.run('ETHUSD')
        if response:
            ticker = json.loads(response.decode())
            price = float(ticker['result']['XETHZUSD']['c'][0])
            self.pricevar.set('{:.2f} USD'.format(price))
        else:
            log.warning('No response.')
        self.root.after(3000, self.query_price)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main = Main()
    main.run()
