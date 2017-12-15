import random
from microraiden.proxy.resources import Expensive
from flask import make_response, request, render_template_string
import io
import os

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
        with open(os.path.join(os.path.dirname(__file__), 'templates', 'fortunes.html')) as fp:
            self.template = fp.read()

    def get(self, url):
        fortune = self.fortunes.get()
        if 'text/html' in request.accept_mimetypes:
            if '―' in fortune:
                fortune, author = [f.strip() for f in fortune.rsplit('―', 1)]
            else:
                fortune, author = fortune, ''
            fortune = fortune.replace('\n', ' ').strip()
            headers = {'Content-Type': 'text/html; charset=utf-8'}
            return render_template_string(
                self.template,
                fortune=fortune,
                author=author,
                back_url='/',
            ), 200, headers
        else:
            headers = {'Content-Type': 'text/plain; charset=utf-8'}
            return make_response(fortune, 200, headers)
