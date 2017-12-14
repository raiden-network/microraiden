from .fortunes import PaywalledFortune
from .wikipaydia import PaywalledWikipedia
from microraiden.proxy.resources import Expensive
from flask import make_response


class PaywalledDoggo(Expensive):
    def get(self, url):
        doggo_str = """
             |\_/|
             | @ @   Woof!
             |   <>              _
             |  _/\------____ ((| |))
             |               `--' |
         ____|_       ___|   |___.'
        /_/_____/____/_______|
        """
        headers = {"Content-Type": 'text/ascii'}
        return make_response(doggo_str, 200, headers)


class PaywalledTeapot(Expensive):
    def get(self, url):
        return "HI I AM A TEAPOT", 418


class PaywalledEchoFix(Expensive):
    def get(self, url):
        return url.split('/')[-1]


__all__ = (
    PaywalledDoggo,
    PaywalledTeapot,
    PaywalledFortune,
    PaywalledWikipedia
)
