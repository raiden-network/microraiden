import gevent

from flask import Flask, safe_join
from flask_restful import (
    Api,
)


from microraiden.channel_manager import (
    ChannelManager
)

from microraiden.proxy.resources import (
    Expensive,
    ChannelManagementAdmin,
    ChannelManagementAdminChannels,
    ChannelManagementListChannels,
    ChannelManagementChannelInfo,
    ChannelManagementLogin,
    ChannelManagementLogout,
    ChannelManagementRoot,
    ChannelManagementStats,
)

from microraiden.proxy.resources.expensive import LightClientProxy
from microraiden.constants import API_PATH, HTML_DIR, JSLIB_DIR, JSPREFIX_URL
from microraiden.proxy.resources.paywall_decorator import Paywall


import logging
import ssl

log = logging.getLogger(__name__)


class PaywalledProxy:
    def __init__(
            self,
            channel_manager: ChannelManager,
            flask_app=None,
            paywall_html_dir=None,
            paywall_js_dir=None
    ):
        #  this doesn't work atm, due to test teardown problems
        #  it's not a critical error, but it should be fixed
        #  gevent.get_hub().SYSTEM_ERROR += (BaseException, )
        paywall_html_dir = paywall_html_dir or HTML_DIR
        paywall_js_dir = paywall_js_dir or JSLIB_DIR
        assert isinstance(channel_manager, ChannelManager)
        assert isinstance(paywall_html_dir, str)

        if not flask_app:
            self.app = Flask(
                __name__,
                static_url_path=JSPREFIX_URL,
                static_folder=paywall_js_dir
            )
        else:
            assert isinstance(flask_app, Flask)
            self.app = flask_app

        self.api = Api(self.app)
        self.rest_server = None
        self.server_greenlet = None

        self.channel_manager = channel_manager
        self.channel_manager.start()

        self.light_client_proxy = LightClientProxy(safe_join(paywall_html_dir, "index.html"))
        self.paywall = Paywall(channel_manager, self.light_client_proxy)

        # REST interface
        self.api.add_resource(ChannelManagementLogin, API_PATH + "/login")
        self.api.add_resource(ChannelManagementLogout, API_PATH + "/logout")
        self.api.add_resource(ChannelManagementChannelInfo,
                              API_PATH + "/channels/<string:sender_address>/<int:opening_block>",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementAdmin,
                              API_PATH + "/admin",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementAdminChannels,
                              API_PATH +
                              "/admin/channels/<string:sender_address>/<int:opening_block>",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementListChannels,
                              API_PATH + "/channels/",
                              API_PATH + "/channels/<string:sender_address>",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementStats,
                              API_PATH + "/stats",
                              resource_class_kwargs={'channel_manager': self.channel_manager})
        self.api.add_resource(ChannelManagementRoot, "/cm")

    def run(self,
            host: str='localhost',
            port: int=5000, debug:
            bool=False,
            ssl_context: list=None
            ):
        """Start the proxy/WSGI server"""
        assert ssl_context is None or len(ssl_context) == 2
        # register our custom error handler to ignore some exceptions and fail on others
#        register_error_handler(self.gevent_error_handler)
        self.channel_manager.wait_sync()
        from gevent.pywsgi import WSGIServer
        if ((ssl_context is not None) and
           (len(ssl_context) == 2) and
           (ssl_context[0] and ssl_context[1])):
            self.rest_server = WSGIServer((host, port), self.app,
                                          keyfile=ssl_context[0],
                                          certfile=ssl_context[1])
        else:
            self.rest_server = WSGIServer((host, port), self.app)
        self.server_greenlet = gevent.spawn(self.rest_server.serve_forever)

    def stop(self):
        assert self.rest_server is not None
        assert self.server_greenlet is not None
        # we should stop the server only if it has been started. In case we do stop()
        #  right after start(), the server may be in an undefined state and join() will
        #  hang indefinetely (this often happens with tests)
        for try_n in range(5):
            if self.rest_server.started is True:
                break
            gevent.sleep(1)
        self.rest_server.stop()
        self.server_greenlet.join()

    def join(self):
        """Block until server greenlet/Proxy stops"""
        try:
            self.server_greenlet.join()
        finally:
            self.channel_manager.stop()

    @staticmethod
    def gevent_error_handler(context, exc_info):
        e = exc_info[1]
        # recover if HTTP request is done to a HTTPS endpoint
        if isinstance(e, ssl.SSLError) and e.reason == 'HTTP_REQUEST':
            return
        gevent.get_hub().handle_system_error(exc_info[0], exc_info[1])

    def add_paywalled_resource(self, cls: Expensive, url: str, price: int=None, *args, **kwargs):
        cfg = {
            'channel_manager': self.channel_manager,
            'light_client_proxy': self.light_client_proxy,
            'price': price,
            'paywall': self.paywall
        }
        if 'resource_class_kwargs' in kwargs:
            cfg.update(kwargs.pop('resource_class_kwargs'))
        if 'endpoint' not in kwargs:
            kwargs['endpoint'] = url.replace('/', '_')
        return self.api.add_resource(cls, url, resource_class_kwargs=cfg, *args, **kwargs)
