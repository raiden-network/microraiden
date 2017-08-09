import os
import sys
#
# Flask restarts itself when a file changes, but this restart
#  does not have PYTHONPATH set properly if you start the
#  app with python -m raiden_mps.
#
if __package__ is None:
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    sys.path.insert(0, path + "/../")


def main():
    blockchain = BlockchainMock(None, None)
    app = PaymentProxy(blockchain)
    app.run(debug=True)


from raiden_mps.proxy.server_flask import PaymentProxy
from raiden_mps.test.utils import BlockchainMock

if __name__ == '__main__':
    main()
