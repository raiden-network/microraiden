import logging
import click
import os

from microraiden.click_helpers import main, pass_app
from microraiden.proxy import PaywalledProxy
from microraiden.make_helpers import make_paywalled_proxy
from microraiden.proxy.resources import PaywalledProxyUrl


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


@main.command()
@click.option(
    '--host',
    default='localhost',
    help='Address of the proxy'
)
@click.option(
    '--port',
    default=5000,
    help='Port of the proxy'
)
@pass_app
def start(app, host, port):
    app.run(host=host, port=port, debug=True)  # nosec
    proxy = ETHTickerProxy(proxy=app)
    proxy.app.join()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
