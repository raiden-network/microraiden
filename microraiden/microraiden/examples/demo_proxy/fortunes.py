import random
from microraiden.proxy.content import PaywalledContent
from flask import make_response


class Fortunes:
    def __init__(self, fortunes_file):
        fp = open(fortunes_file, 'r')
        self.quotes = Fortunes.load(fp)

    @staticmethod
    def load(fp):
        ret = []
        quote = ''
        for line in fp.readlines():
            if line.strip() == '%':
                ret.append(quote)
                quote = ''
            else:
                quote += line
        return ret

    def get(self):
        return random.choice(self.quotes)


class PaywalledFortune(PaywalledContent):
    def __init__(self, path, price, filepath):
        super(PaywalledFortune, self).__init__(path, price)
        self.fortunes = Fortunes(filepath)

    def get(self, url):
        headers = {'Content-Type': 'text/plain; charset=utf-8'}
        return make_response(self.fortunes.get(), 200, headers)
