import inspect
from typing import Any, Dict, Callable


def get_function_kwargs(kwargs: Dict[str, Any], function: Callable):
    return {
        kw: arg for kw, arg in kwargs.items()
        if kw in inspect.signature(function).parameters
    }


def pop_function_kwargs(kwargs: Dict[str, Any], function: Callable):
    function_kwargs = get_function_kwargs(kwargs, function)
    for kw in function_kwargs:
        kwargs.pop(kw)

    return function_kwargs
