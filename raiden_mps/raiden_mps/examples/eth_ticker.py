import json
from tkinter import ttk
import tkinter
import logging

from raiden_mps import Client, DefaultHTTPClient
from raiden_mps.test.config import TEST_SENDER_PRIVKEY, TEST_RECEIVER_PRIVKEY
from raiden_mps.proxy.content import PaywalledProxyUrl
from raiden_mps.proxy.paywalled_proxy import PaywalledProxy
from raiden_mps.utils import make_channel_manager

log = logging.getLogger(__name__)


def start_proxy():
    cm = make_channel_manager(TEST_RECEIVER_PRIVKEY, 'eth_ticker_proxy.pkl')
    app = PaywalledProxy(cm)
    app.add_content(PaywalledProxyUrl(
        "[A-Z]{6}",
        1,
        lambda request: 'api.bitfinex.com/v1/pubticker/' + request
    ))
    app.run(debug=True)
    return app


class Main(ttk.Frame):
    def __init__(self):
        self.root = tkinter.Tk()
        ttk.Frame.__init__(self, self.root)
        self.root.title('µRaiden ETH Ticker')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.pack()
        self.pricevar = tkinter.StringVar(value='0.00 USD')
        ttk.Label(self, textvariable=self.pricevar, font=('Helvetica', '72')).pack()

        self.app = start_proxy()
        self.client = Client(TEST_SENDER_PRIVKEY)
        self.httpclient = DefaultHTTPClient(
            self.client,
            'localhost',
            5000,
            initial_deposit=lambda x: 20 * x,
            topup_deposit=lambda x: 10 * x
        )
        self.running = False

    def run(self):
        self.root.after(1000, self.query_price)
        self.running = True
        self.root.mainloop()

    def query_price(self):
        if not self.running:
            return

        response = self.httpclient.run('ETHUSD')
        if response:
            ticker = json.loads(response.decode())
            price = float(ticker['last_price'])
            log.info('New price received: {:.2f} USD'.format(price))
            self.pricevar.set('{:.2f} USD'.format(price))
        else:
            log.warning('No response.')

        self.root.after(5000, self.query_price)

    def close(self):
        log.info('Shutting down gracefully.')
        self.running = False
        self.root.destroy()
        self.httpclient.stop()
        self.httpclient.close_active_channel()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main = Main()
    main.run()
