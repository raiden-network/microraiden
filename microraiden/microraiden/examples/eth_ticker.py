import json
from tkinter import ttk
import tkinter
import logging
import gevent

import click
import os

from microraiden import Client, DefaultHTTPClient
from microraiden.crypto import privkey_to_addr
from microraiden.config import CHANNEL_MANAGER_ADDRESS
from microraiden.proxy.content import PaywalledProxyUrl
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.make_helpers import make_paywalled_proxy

log = logging.getLogger(__name__)


def start_proxy(receiver_privkey: str) -> PaywalledProxy:
    state_file_name = '{}_{}.json'.format(
        CHANNEL_MANAGER_ADDRESS, privkey_to_addr(receiver_privkey)
    )
    app_dir = click.get_app_dir('microraiden')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    app = make_paywalled_proxy(receiver_privkey, os.path.join(app_dir, state_file_name))
    app.add_content(PaywalledProxyUrl(
        "[A-Z]{6}",
        1,
        'http://api.bitfinex.com/v1/pubticker/',
        [r'[A-Z]{6}']
    ))
    app.run()
    return app


class ETHTickerProxy:
    def __init__(self, privkey: str, proxy: PaywalledProxy = None):
        if proxy:
            self.app = proxy
            self.app.add_content(PaywalledProxyUrl(
                "[A-Z]{6}",
                1,
                'http://api.bitfinex.com/v1/pubticker/',
                [r'[A-Z]{6}']
            ))
        else:
            self.app = start_proxy(privkey)

    def stop(self):
        self.app.stop()


class ETHTickerClient(ttk.Frame):
    def __init__(
            self,
            sender_privkey: str,
            httpclient: DefaultHTTPClient = None
    ):
        self.root = tkinter.Tk()
        ttk.Frame.__init__(self, self.root)
        self.root.title('µRaiden ETH Ticker')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.pack()
        self.pricevar = tkinter.StringVar(value='0.00 USD')
        ttk.Label(self, textvariable=self.pricevar, font=('Helvetica', '72')).pack()

        if httpclient:
            self.httpclient = httpclient
            self.client = httpclient.client
        else:
            self.client = Client(sender_privkey)
            self.httpclient = DefaultHTTPClient(
                self.client,
                'localhost',
                5000,
                initial_deposit=lambda x: 10 * x,
                topup_deposit=lambda x: 5 * x
            )

        self.active_query = False
        self.running = False

    def run(self):
        self.running = True
        self.root.after(1000, self.query_price)
        self.root.mainloop()

    def query_price(self):
        if not self.running:
            return
        self.active_query = True

        response = self.httpclient.run('ETHUSD')
        if response:
            ticker = json.loads(response.decode())
            price = float(ticker['last_price'])
            log.info('New price received: {:.2f} USD'.format(price))
            self.pricevar.set('{:.2f} USD'.format(price))
        else:
            log.warning('No response.')

        if self.running:
            self.root.after(5000, self.query_price)
        self.active_query = False

    def close(self):
        log.info('Shutting down gracefully.')
        self.running = False
        self.root.destroy()
        self.httpclient.stop()
        # Sloppy handling of thread joining but works for this small demo.
        while self.active_query:
            gevent.sleep(1)

        self.httpclient.close_active_channel()
        self.client.close()


@click.command()
@click.option('--start-proxy/--no-proxy', default=False)
def main(start_proxy):
    proxy = None
    ticker = None
    receiver_privkey = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    sender_privkey = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    try:
        if start_proxy:
            proxy = ETHTickerProxy(receiver_privkey)
        ticker = ETHTickerClient(sender_privkey)
        ticker.run()
    except KeyboardInterrupt:
        if ticker:
            ticker.close()
        if proxy is not None:
            proxy.stop()


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.INFO)
    main()
