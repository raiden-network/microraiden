"""A very basic demonstration of usage of the Proxy.
You can use this as a template for your own app.
"""
import click
import os
import logging
from flask import send_file

from microraiden.click_helpers import main, pass_app
from microraiden.constants import TKN_DECIMALS
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
@click.option(
    '--index-file',
    default=None,
    help='Path to landing page file (to be shown in /)',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@pass_app
def start(app, host, port, index_file):
    fortunes_en = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/fortunes'))
    fortunes_cn = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/chinese'))
    app.add_paywalled_resource(PaywalledFortune, '/fortunes_en', 1 * TKN_DECIMALS,
                               resource_class_args=(fortunes_en,))
    app.add_paywalled_resource(PaywalledFortune, '/fortunes_cn', 1 * TKN_DECIMALS,
                               resource_class_args=(fortunes_cn,))
    app.add_paywalled_resource(PaywalledDoggo, '/doggo.txt', price=2 * TKN_DECIMALS)
    app.add_paywalled_resource(PaywalledTeapot, '/teapot', 3 * TKN_DECIMALS)

    if index_file:
        app.app.add_url_rule('/', 'index', lambda: send_file(index_file))

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
