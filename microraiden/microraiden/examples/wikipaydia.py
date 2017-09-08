import click

from microraiden.proxy.content import (
    PaywalledProxyUrl
)
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
    app.add_content(PaywalledProxyUrl(".*", 1, "http://en.wikipedia.org/", [r"wiki/.*"]))
    app.run(host=host, port=port, debug=True)
    app.join()


if __name__ == '__main__':
    import logging
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("blockchain").setLevel(logging.DEBUG)
    logging.getLogger("channel_manager").setLevel(logging.DEBUG)
    main()
