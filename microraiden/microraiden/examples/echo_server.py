"""
This is dummy code showing how the minimal app could look like.
In his case we don't use a proxy, but directly a server
"""
import os
import click
from microraiden.examples.demo_resources import (
    PaywalledEchoFix,
)

from microraiden.make_helpers import make_paywalled_proxy
from microraiden.config import TKN_DECIMALS

if __name__ == '__main__':
    private_key = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    state_file_name = 'echo_server.json'
    app_dir = click.get_app_dir('microraiden')
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    state_file_name = os.path.join(app_dir, state_file_name)
    # set up a paywalled proxy
    # arguments are:
    #  - private key to use for receiving funds
    #  - file for storing state information (balance proofs)
    app = make_paywalled_proxy(private_key, state_file_name)

    # Add resource defined by regex and with a fixed price of 1 token
    app.add_content(PaywalledEchoFix,
                    "echofix/<string:param>", price=1 * TKN_DECIMALS
                    )
    # Resource with a price determined by the second parameter
    app.add_content(PaywalledEchoFix,
                    "echodyn\/<int:param>",
                    price=lambda request: int(request.split("/")[1]) * TKN_DECIMALS
                    )
    # start the app. proxy is a WSGI greenlet, so you must join it properly
    app.run(debug=True)
    app.join()
    # now use echo_client to get the resources
