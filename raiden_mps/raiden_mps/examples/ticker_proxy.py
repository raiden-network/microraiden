from raiden_mps.examples.eth_ticker import ETHTickerProxy
from raiden_mps.test.config import TEST_RECEIVER_PRIVKEY
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    proxy = ETHTickerProxy(TEST_RECEIVER_PRIVKEY)
    proxy.app.join()
    proxy.stop()
