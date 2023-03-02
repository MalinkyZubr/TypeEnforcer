import typing
import types


try:
    from . import exceptions as exc
except:
    import exceptions as exc


class TypeEnforcer:
    @staticmethod
    def __check_args(hints: dict, args: tuple, func: typing.Callable) -> None:
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
    def __combine_args_kwargs(args: tuple, kwargs: dict, func: typing.Callable) -> dict:
        args_limit = len(args)
        args_dict: dict = {}
        for index, arg_name in list(enumerate(func.__code__.co_varnames))[:args_limit]:
            args_dict.update({arg_name:args[index]})
        args_dict.update(kwargs)

        print(args_dict)
        return args_dict
    
    @staticmethod
    def __generate_hints_dict(args: dict, func: typing.Callable) -> dict:
        incomplete_hints = typing.get_type_hints(func)
        complete_hints: dict = dict()
        
        for arg_name in args.keys():
            try:
                complete_hints.update({arg_name:incomplete_hints[arg_name]})
            except KeyError:
                complete_hints.update({arg_name:typing.Any})
        
        return complete_hints

    @staticmethod
    def enforcer(func: typing.Callable):
        """
        add as a decorator to any python function 

        Enforces python type hints. 
        Parameters and returns that do not have explicit hints will be assumed to have types of typing.Any
        Supports basic type hinting operations, like Type[], Union[], and <Container>[<datatype>]

        Must also use hints for the return type, following same rules as the parameters

        good for debugging
        """
        def inner(*args, **kwargs):
            concat_args = TypeEnforcer.__combine_args_kwargs(args, kwargs, func)
            hints = TypeEnforcer.__generate_hints_dict(concat_args, func)
            defaults: list = []
            if 'return' in hints.keys():
                return_type = hints['return']
                hints.pop('return')
            else: 
                return_type = typing.Any

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
            if 'return' in hints and type(return_value) != return_type and return_type not in typing.get_args(return_type) and return_type != typing.Any:
                raise exc.WrongReturnType(return_type, type(return_value))
            return return_value
        return inner


if __name__ == "__main__":
    class Silly:
        pass

    class Doof(Silly):
        pass

    @TypeEnforcer.enforcer
    def foo(n, v: typing.Callable, f: list[str], x: typing.Any, y: str, z: bool | None=True, a: str="hello", ):
        return True

    def zoo():
        pass

    x = foo(Doof(), zoo, ['r'], 1, "hi", z=None)
    print(x)

    print(type(foo))
    print(type(typing.Callable))
