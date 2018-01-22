from tkinter import ttk
import tkinter
import logging
import gevent

import click
import os

from microraiden import Session
from microraiden.proxy import PaywalledProxy
from microraiden.proxy.resources import PaywalledProxyUrl
from microraiden.make_helpers import make_paywalled_proxy

log = logging.getLogger(__name__)


def start_proxy(receiver_privkey: str) -> PaywalledProxy:
    state_file_name = 'ticker_proxy.db'
    app_dir = click.get_app_dir('microraiden')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    app = make_paywalled_proxy(receiver_privkey, os.path.join(app_dir, state_file_name))
    app.run()
    return app


class ETHTickerProxy:
    def __init__(self, privkey: str = None, proxy: PaywalledProxy = None) -> None:
        assert privkey or proxy
        if proxy:
            self.app = proxy
        else:
            self.app = start_proxy(privkey)
        cfg = {'resource_class_kwargs': {
               'domain': 'http://api.bitfinex.com/v1/pubticker/'}
               }
        self.app.add_paywalled_resource(
            PaywalledProxyUrl,
            '/<string:ticker>',
            100,
            **cfg
        )

    def stop(self):
        self.app.stop()


class ETHTickerClient(ttk.Frame):
    def __init__(
            self,
            sender_privkey: str,
            session: Session = None,
            poll_interval: float = 5
    ) -> None:
        self.poll_interval = poll_interval

        self.root = tkinter.Tk()
        ttk.Frame.__init__(self, self.root)
        self.root.title('µRaiden ETH Ticker')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.pack()
        self.pricevar = tkinter.StringVar(value='0.00 USD')
        ttk.Label(self, textvariable=self.pricevar, font=('Helvetica', '72')).pack()

        if session is None:
            self.session = Session(
                private_key=sender_privkey,
                close_channel_on_exit=True,
                endpoint_url='http://localhost:5000'
            )
        else:
            self.session = session

        self.active_query = False
        self.running = False

    def run(self):
        self.running = True
        self.root.after(0, self.query_price)
        self.root.mainloop()

    def query_price(self):
        if not self.running:
            return
        self.active_query = True

        response = self.session.get('http://localhost:5000/ETHUSD')
        if response:
            price = float(response.json()['last_price'])
            log.info('New price received: {:.2f} USD'.format(price))
            self.pricevar.set('{:.2f} USD'.format(price))
        else:
            log.warning('No response.')

        if self.running:
            self.root.after(int(self.poll_interval * 1000), self.query_price)
        self.active_query = False

    def close(self):
        log.info('Shutting down gracefully.')
        self.running = False
        self.root.destroy()
        # Sloppy handling of thread joining but works for this small demo.
        while self.active_query:
            gevent.sleep(1)

        self.session.close()


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
