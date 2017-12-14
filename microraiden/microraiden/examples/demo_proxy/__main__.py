import click
import os
import logging

from microraiden.click_helpers import main, pass_app
from microraiden.config import TKN_DECIMALS
from microraiden.examples.demo_resources import (
    PaywalledDoggo,
    PaywalledFortune,
    PaywalledTeapot
)


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
    fortunes_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/fortunes'))
    app.add_paywalled_resource(PaywalledDoggo, '/doggo.txt', price=2 * TKN_DECIMALS)
    app.add_paywalled_resource(PaywalledFortune, '/wisdom', 1 * TKN_DECIMALS,
                               resource_class_args=(fortunes_path,))
    app.add_paywalled_resource(PaywalledTeapot, '/teapot', 3 * TKN_DECIMALS)
    app.run(host=host, port=port, debug=True)  # nosec
    app.join()


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()
