"""
This is dummy code showing how the minimal app could look like.
In his case we don't use a proxy, but directly a server
"""
import os
import click
from microraiden.proxy.content import (
    PaywalledContent,
    PaywalledProxyUrl
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
    # We setup the resource to return whatever is supplied as a second argument
    #  in the URL.
    app.add_content(PaywalledContent(
                    "echofix\/[a-zA-Z0-9]+", 1 * TKN_DECIMALS,
                    lambda request: (request.split("/")[1], 200)))
    # Resource with a price determined by the second parameter
    app.add_content(PaywalledContent(
                    "echodyn\/[0-9]+",
                    lambda request: int(request.split("/")[1]) * TKN_DECIMALS,
                    lambda request: (int(request.split("/")[1]), 200)))
    app.add_content(PaywalledProxyUrl(
                    "p\/[0-9]+",
                    1 * TKN_DECIMALS,
                    lambda request: 'google.com/search?q=' + request.split("/")[1]))
    # start the app. proxy is a WSGI greenlet, so you must join it properly
    app.run(debug=True)
    app.join()
    # now use echo_client to get the resources
