import click
import os
from microraiden.click_helpers import main, pass_app
from flask import make_response
import logging

from microraiden.proxy.content import (
    PaywalledContent,
)
from .fortunes import PaywalledFortune


def get_doggo(_):
    doggo_str = """
         |\_/|
         | @ @   Woof!
         |   <>              _
         |  _/\------____ ((| |))
         |               `--' |
     ____|_       ___|   |___.'
    /_/_____/____/_______|
    """
    headers = {"Content-type": 'text/ascii'}
    return make_response(doggo_str, 200, headers)


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
    app.add_content(PaywalledContent("doggo", 2, get_doggo))
    app.add_content(PaywalledFortune("wisdom", 1, fortunes_path))
    app.add_content(PaywalledContent("teapot", 3, lambda _: ("HI I AM A TEAPOT", 418)))
    app.run(host=host, port=port, debug=True)
    app.join()


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()
