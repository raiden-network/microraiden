from microraiden.examples.eth_ticker import ETHTickerProxy
import logging
import click
from microraiden.click_helpers import main, pass_app


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
