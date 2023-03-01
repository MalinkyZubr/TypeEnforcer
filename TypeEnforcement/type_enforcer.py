import typing
import types


try:
    from . import exceptions as exc
except:
    import exceptions as exc


class TypeEnforcer:
    @staticmethod
    def __check_args(hints: dict, args: tuple, func: typing.Callable):
        for argument_name, argument in args.items():
            received_type = type(argument)
            expected_type = hints[argument_name]
            try:
                if issubclass(received_type, expected_type):
                    continue
            except TypeError:
                pass
            if (received_type != expected_type 
                and received_type not in typing.get_args(expected_type)
                and expected_type != typing.Any
                ):
                raise exc.WrongParameterType(func.__name__,argument_name,received_type,expected_type)

    @staticmethod
    def __combine_args_kwargs(args: tuple, kwargs: dict, hints: dict):
        args_limit = len(args)
        args_dict: dict = {}
        for index, item in list(enumerate(hints.items()))[:args_limit]:
            key, value = item
            args_dict.update({key:args[index]})
        args_dict.update(kwargs)

        return args_dict

    @staticmethod
    def enforcer(func: typing.Callable):
        """
        Enforces python type hints. 
        Ensure that all of the function parameters have type hints! Even if it is just typing.Any
        Supports basic type hinting operations, like Type[], Union[], and <Container>[<datatype>]
        
        good for debugging
        """
        def inner(*args, **kwargs):
            hints = typing.get_type_hints(func)

            concat_args = TypeEnforcer.__combine_args_kwargs(args, kwargs, hints)

            defaults: dict = []
            return_type = hints['return']
            hints.pop('return')

            for key in hints.keys():
                if type(hints[key]) == types.GenericAlias:
                    hints[key] = hints[key].__origin__
                try:
                    if hints[key].__origin__ == type:
                        hints[key] = hints[key].__args__
                except AttributeError:
                    pass
                if key not in concat_args:
                    defaults += key
            for default in defaults:
                hints.pop(default)

            TypeEnforcer.__check_args(hints, concat_args, func)

            return_value = func(*args, **kwargs)
            if type(return_value) != return_type and return_type not in typing.get_args(return_type) and return_type != typing.Any:
                raise exc.WrongReturnType(return_type, type(return_value))
            return return_value
        return inner


if __name__ == "__main__":
    class Silly:
        pass

    class Doof(Silly):
        pass

    @TypeEnforcer.enforcer
    def foo(n: typing.Type[Silly], f: list[str], x: typing.Any, y: str, z: bool | None=True, a: str="hello") -> bool:
        return True

    x = foo(Doof(), ['r'], 1, "hi", z=None, a="yo")
    print(x)
