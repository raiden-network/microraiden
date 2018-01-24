from tkinter import ttk
import tkinter
import logging
import gevent
import click
import sys

from microraiden import Session
from microraiden import utils

log = logging.getLogger(__name__)


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
@click.option(
    '--private-key',
    required=True,
    help='Path to private key file of the proxy',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--private-key-password-file',
    default=None,
    help='Path to file containing password for the JSON-encoded private key',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def main(
    private_key,
    private_key_password_file,
):
    private_key = utils.get_private_key(private_key, private_key_password_file)
    if private_key is None:
        sys.exit(1)
    ticker = None
    try:
        ticker = ETHTickerClient(private_key)
        ticker.run()
    except KeyboardInterrupt:
        if ticker:
            ticker.close()


if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    logging.basicConfig(level=logging.INFO)
    main()
