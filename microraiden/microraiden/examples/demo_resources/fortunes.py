import random
from microraiden.proxy.resources import Expensive
from flask import make_response
import io

import logging
log = logging.getLogger(__name__)


class Fortunes:
    def __init__(self, fortunes_file):
        with io.open(fortunes_file, 'r', encoding='utf8') as fp:
            self.quotes = Fortunes.load(fp)

    @staticmethod
    def load(fp):
        ret = []
        quote = ''
        for line in fp:
            if line.strip() == '%':
                ret.append(quote)
                quote = ''
            else:
                quote += line
        return ret

    def get(self):
        log.error("%d" % len(self.quotes))
        return random.choice(self.quotes)  # nosec


class PaywalledFortune(Expensive):
    def __init__(self, filepath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fortunes = Fortunes(filepath)

    def get(self, url):
        headers = {'Content-Type': 'text/plain; charset=utf-8'}
        return make_response(self.fortunes.get(), 200, headers)
