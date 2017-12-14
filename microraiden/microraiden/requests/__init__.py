import inspect

from requests import Response

from microraiden import Session, Client


def request(method: str, url: str, **kwargs) -> Response:
    session_kwargs = {
        kw: arg for kw, arg in kwargs.items()
        if kw in inspect.signature(Session.__init__).parameters
    }
    client_kwargs = {
        kw: arg for kw, arg in kwargs.items()
        if kw in inspect.signature(Client.__init__).parameters
    }

    for kw in session_kwargs:
        kwargs.pop(kw)
    for kw in client_kwargs:
        kwargs.pop(kw)

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
