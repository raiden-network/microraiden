import pytest
import logging
import types
from microraiden import Session, Client

log = logging.getLogger(__name__)


@pytest.fixture
def session(client: Client, use_tester: bool, api_endpoint_address: str):
    # patch request_resource of this instance in order to advance blocks when doing requests
    def request_patched(self: Session, method: str, url: str, **kwargs):
        if use_tester:
            log.info('Mining new block.')
            self.client.context.web3.testing.mine(1)
        return Session._request_resource(self, method, url, **kwargs)

    kwargs = {}
    if use_tester:
        kwargs['retry_interval'] = 0.1

    session = Session(
        client,
        endpoint_url='http://' + api_endpoint_address,
        **kwargs
    )
    session._request_resource = types.MethodType(request_patched, session)
    yield session
    session.close()
