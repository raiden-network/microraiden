from typing import Any

from microraiden.utils.misc import get_function_kwargs, pop_function_kwargs


def test_get_function_kwargs():
    def function(a: str, b: int, something: Any):
        pass

    kwargs = dict(b=5, c='string', something=3.14)
    function_kwargs = get_function_kwargs(kwargs, function)
    assert function_kwargs == dict(b=5, something=3.14)


def test_pop_function_kwargs():
    def function(a: str, b: int, something: Any):
        pass

    kwargs = dict(b=5, c='string', something=3.14)
    function_kwargs = pop_function_kwargs(kwargs, function)
    assert function_kwargs == dict(b=5, something=3.14)
    assert kwargs == dict(c='string')
