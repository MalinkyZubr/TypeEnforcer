import typing
import types


try:
    from . import exceptions as exc
except:
    import exceptions as exc


class TypeEnforcer:
    __allowed_for_recursive_checking: list = [dict, list, tuple, set]
    @staticmethod
    def __check_args(hints: dict, args: tuple, func: typing.Callable, recursive: bool) -> None:
        for argument_name, argument in args.items():
            received_type = type(argument)
            expected_type = hints[argument_name]
            try:
                if issubclass(received_type, expected_type):
                    continue
            except TypeError:
                pass
            if recursive and type(expected_type) == types.GenericAlias:
                TypeEnforcer.__generic_alias_checker(expected_type, argument, argument_name, func.__name__)
            elif (received_type != expected_type 
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
    def __generic_alias_checker(data_type: types.GenericAlias, data: typing.Any, parent_variable_name: str, func_name: str, is_return: bool=False):
        if type(data_type) == types.GenericAlias:
            print(data_type.__origin__)
            print(data_type.__args__)
            if type(data) != data_type.__origin__:
                if is_return:
                    raise exc.WrongReturnType(data_type, type(data))
                else:
                    raise exc.WrongParameterType(func_name, parent_variable_name, data_type, data)
            print(data_type.__args__)
            if isinstance(data, typing.Iterable) and not isinstance(data, str):
                for item in data:
                    TypeEnforcer.__generic_alias_checker(data_type.__args__[0], item, parent_variable_name, func_name)
            if isinstance(data, dict):
                for key, value in data.items():
                    TypeEnforcer.__generic_alias_checker(data_type.__args__[0], key, parent_variable_name, func_name)
                    TypeEnforcer.__generic_alias_checker(data_type.__args__[1], value, parent_variable_name, func_name)
        elif data_type != type(data) and data_type != typing.Any:
            if is_return:
                raise exc.WrongReturnType(data_type, type(data))
            else:
                raise exc.WrongParameterType(func_name, f"Nested variable in {parent_variable_name}", data_type, type(data))

    @staticmethod
    def enforcer(recursive:bool=False):
        """
        add as a decorator to any python function 

        Enforces python type hints. 
        Parameters and returns that do not have explicit hints will be assumed to have types of typing.Any
        Supports basic type hinting operations, like Type[], Union[], and GenericAlias objects like dict[] and list[]

        Supports recursive type checking in runtime! If you want to check that the contents in a deep nested datastructure match type hints,
        just enable recursive type checking with "recursive=True". Note that this significantly increases the computation necessary to run functions
        so it is advisable to only run this during the debugging phase of development. Note that as of now this only works with lists, tuples, sets, and dicts

        Overall, best used with debugging
        """
        def enforcement(func: typing.Callable):
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
                    if type(hints[key]) == types.GenericAlias and not recursive:
                        hints[key] = hints[key].__origin__
                    elif type(hints[key]) == types.GenericAlias:
                        if hints[key] not in TypeEnforcer.__allowed_for_recursive_checking:
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

                TypeEnforcer.__check_args(hints, concat_args, func, recursive=recursive)

                return_value = func(*args, **kwargs)
                if 'return' in hints:
                    if type(return_type) == types.GenericAlias:
                        TypeEnforcer.__generic_alias_checker(return_type, return_value, 'return', func.__name__, is_return=True)
                    elif type(return_value) != return_type and return_type not in typing.get_args(return_type) and return_type != typing.Any:
                        raise exc.WrongReturnType(return_type, type(return_value))
                return return_value
            return inner
        return enforcement


if __name__ == "__main__":
    class Silly:
        pass

    class Doof(Silly):
        pass

    @TypeEnforcer.enforcer(recursive=True)
    def foo(n, h: dict[str, int], v: typing.Callable, f: list[str], x: typing.Any, y: str, z: bool | None=True, a: str="hello") -> list[str]:
        return ["silly" for x in range(10)]

    def zoo():
        pass

    x = foo(Doof(), {"x":2}, zoo, ['r', 'x'], 1, "hi", z=True)
    print(x)

    print(type(foo))
    print(type(typing.Callable))
