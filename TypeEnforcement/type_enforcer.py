import typing
try:
    from . import exceptions as exc
except:
    import exceptions as exc

def check_args(hints: dict, args: tuple, func: typing.Callable):
    for index, item in args.items():
        argument_type_received = type(args[index])
        argument_name, expected_type = item
        print(f"{argument_type_received}++++{expected_type}")
        if argument_type_received != expected_type:
            raise exc.WrongParameterType(func.__name__,argument_name,argument_type_received,expected_type)

def combine_args_kwargs(args: tuple, kwargs: dict, hints: dict):
    args_limit = len(args)
    args_dict: dict = {}
    for index, item in list(enumerate(hints.items()))[:args_limit]:
        key, value = item
        args_dict.update({key:args[index]})
    args_dict.update(kwargs)

    return args_dict

def enforcer(func: typing.Callable):
    def inner(*args, **kwargs):

        hints = typing.get_type_hints(func)

        concat_args = combine_args_kwargs(args, kwargs, hints)

        defaults: dict = []
        return_type = hints['return']
        hints.pop('return')

        for key in hints.keys():
            if key not in concat_args:
                defaults += key
                print(key)
        for default in defaults:
            print(default)
            hints.pop(default)

        print(f"{hints}\n{concat_args}")

        return_value = func(*args, **kwargs)
        if type(return_value) != return_type:
            raise exc.WrongReturnType(return_type, type(return_value))
    return inner

@enforcer
def foo(x: int, y: str, z: bool=True, a: str="hello") -> bool:
    return True

# print(typing.get_type_hints(foo))

x = foo(1, "hi", a="zeugma")
print(x)
