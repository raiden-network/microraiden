from requests import Response

from microraiden import Session, Client
from microraiden.utils import pop_function_kwargs


def request(method: str, url: str, **kwargs) -> Response:
    session_kwargs = pop_function_kwargs(kwargs, Session.__init__)
    client_kwargs = pop_function_kwargs(kwargs, Client.__init__)

    session_kwargs.update(client_kwargs)

    with Session(**session_kwargs) as session:
        return session.request(method, url, **kwargs)


def get(url: str, **kwargs) -> Response:
    kwargs.setdefault('allow_redirects', True)
    return request('GET', url, **kwargs)


def options(url: str, **kwargs) -> Response:
    kwargs.setdefault('allow_redirects', True)
    return request('OPTIONS', url, **kwargs)


def head(url: str, **kwargs) -> Response:
    kwargs.setdefault('allow_redirects', False)
    return request('HEAD', url, **kwargs)


def post(url: str, **kwargs) -> Response:
    return request('POST', url, **kwargs)


def put(url: str, **kwargs) -> Response:
    return request('PUT', url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    return request('PATCH', url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    return request('DELETE', url, **kwargs)
