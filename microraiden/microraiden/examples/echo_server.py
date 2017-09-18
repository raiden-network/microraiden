"""
This is dummy code showing how the minimal app could look like.
In his case we don't use a proxy, but directly a server
"""
from microraiden.proxy.paywalled_proxy import PaywalledProxy
from microraiden.config import CHANNEL_MANAGER_ADDRESS
import os
from microraiden.proxy.content import (
    PaywalledContent,
    PaywalledProxyUrl
)

if __name__ == '__main__':
    private_key = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    tempfile = os.path.join(os.path.expanduser('~'), '.raiden/echo_server.pkl')
    # set up a paywalled proxy
    # arguments are:
    #  - channel manager contract
    #  - private key to use for receiving funds
    #  - temporary file for storing state information (balance proofs)
    app = PaywalledProxy(CHANNEL_MANAGER_ADDRESS,
                         private_key,
                         tempfile)

    # Add resource defined by regex and with a fixed price of 1 token
    # We setup the resource to return whatever is supplied as a second argument
    #  in the URL.
    app.add_content(PaywalledContent(
                    "echofix\/[a-zA-Z0-9]+", 1,
                    lambda request: (request.split("/")[1], 200)))
    # Resource with a price determined by the second parameter
    app.add_content(PaywalledContent(
                    "echodyn\/[0-9]+",
                    lambda request: int(request.split("/")[1]),
                    lambda request: (int(request.split("/")[1]), 200)))
    app.add_content(PaywalledProxyUrl(
                    "p\/[0-9]+",
                    1,
                    lambda request: 'google.com/search?q=' + request.split("/")[1]))
    # start the app. proxy is a WSGI greenlet, so you must join it properly
    app.run(debug=True)
    app.join()
    # now use echo_client to get the resources
