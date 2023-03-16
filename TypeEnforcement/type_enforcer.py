import typing
import types


try:
    from . import exceptions as exc
except:
    import exceptions as exc


class TypeEnforcer:
    __allowed_for_recursive_checking: list = [dict, list, set, tuple]
    @staticmethod
    def __check_args(hints: dict, args: dict, func: typing.Callable, recursive: bool, return_check: bool=False) -> None:
        """
        oh goodness
        """
        for argument_name, argument in args.items():
            received_type = type(argument)
            expected_type = hints[argument_name]
            try:
                if issubclass(received_type, expected_type):
                    continue
            except TypeError:
                pass
            if received_type in typing.get_args(expected_type) or expected_type == typing.Any:
                continue
            elif recursive and type(expected_type) == types.UnionType:
                type_origins_union = [expected for expected in typing.get_args(expected_type) if type(expected) == types.GenericAlias and received_type == expected.__origin__]
                if not type_origins_union and not return_check:
                    raise exc.WrongParameterType(func.__name__,argument_name,received_type,expected_type)
                elif not type_origins_union:
                    raise exc.WrongReturnType(expected_type, received_type)
                elif len(type_origins_union) == 1:
                    TypeEnforcer.__generic_alias_checker(type_origins_union[0], type_origins_union[0], argument, argument_name, func.__name__, is_return=return_check)
                else: # MIGRATE TO THE RECURSIVE TYPE CHECKER FUNCTION
                    fail_count = 0
                    for expected in type_origins_union:
                        try:
                            TypeEnforcer.__generic_alias_checker(expected, expected, argument, argument_name, func.__name__, is_return=return_check)
                            break
                        except (exc.WrongParameterType, exc.WrongReturnType,):
                            fail_count += 1
                        if fail_count == len(type_origins_union) and return_check:
                            raise exc.WrongReturnType(expected_return_type=expected_type, actual_return_type=received_type)
                        elif fail_count == len(type_origins_union) and not return_check:
                            raise exc.WrongParameterType(function_name=func.__name__, parameter_name=argument_name,received_type=received_type, expected_type=expected_type)

            elif recursive and type(expected_type) == types.GenericAlias:
                TypeEnforcer.__generic_alias_checker(expected_type, expected_type, argument, argument_name, func.__name__, is_return=return_check)
            elif (received_type != expected_type):
                if not return_check:
                    raise exc.WrongParameterType(func.__name__,argument_name,received_type,expected_type)
                raise exc.WrongReturnType(expected_type, received_type)

    @staticmethod
    def __combine_args_kwargs(args: tuple, kwargs: dict, func: typing.Callable) -> dict:
        args_limit = len(args)
        args_dict: dict = {}
        for index, arg_name in list(enumerate(func.__code__.co_varnames))[:args_limit]:
            args_dict.update({arg_name:args[index]})
        args_dict.update(kwargs)

        return args_dict
    
    @staticmethod
    def __generate_hints_dict(args: dict, func: typing.Callable) -> dict:
        incomplete_hints = typing.get_type_hints(func)
        if 'return' in incomplete_hints.keys():
            return_type = incomplete_hints['return']
            incomplete_hints.pop('return')
        else: 
            return_type = typing.Any

        complete_hints: dict = dict()
        
        for arg_name in args.keys():
            try:
                complete_hints.update({arg_name:incomplete_hints[arg_name]})
            except KeyError:
                complete_hints.update({arg_name:typing.Any})
        
        return complete_hints, return_type
    
    @staticmethod
    def __generic_alias_checker(data_type: types.GenericAlias, parent_data_type: types.GenericAlias, data: typing.Any, parent_variable_name: str, func_name: str, is_return: bool=False, previous_index=""):
        if type(data_type) == types.GenericAlias:
            if type(data) != data_type.__origin__:
                if is_return:
                    raise exc.WrongReturnType(data_type, type(data))
                else:
                    raise exc.WrongParameterType(func_name, parent_variable_name, type(data), data_type)
            if isinstance(data, typing.Iterable) and not isinstance(data, str) and not isinstance(data, dict):
                if len(data_type.__args__) == 1:
                    for index, item in enumerate(data):
                        TypeEnforcer.__generic_alias_checker(data_type.__args__[0], parent_data_type, item, parent_variable_name, func_name, is_return, previous_index=previous_index+f"[{index}]")
                elif len(data) == len(data_type.__args__):
                    for index, dtype_item_tup in enumerate(zip(data_type.__args__, data)):
                        dtype, item = dtype_item_tup
                        TypeEnforcer.__generic_alias_checker(dtype, parent_data_type, item, parent_variable_name, func_name, is_return, previous_index=previous_index+f"[{index}]")
                else:
                    raise AttributeError(f"The argument {parent_variable_name} received a {data_type} of length {len(data)} when it wanted a length of {len(data_type.__args__)}")
            elif isinstance(data, dict):
                for index, value in data.items():
                    TypeEnforcer.__generic_alias_checker(data_type.__args__[0], parent_data_type, index, parent_variable_name, func_name, is_return, previous_index=previous_index+f"[{index}]")
                    TypeEnforcer.__generic_alias_checker(data_type.__args__[1], parent_data_type, value, parent_variable_name, func_name, is_return, previous_index=previous_index+f"[{index}]")
        elif data_type != type(data) and data_type != typing.Any:
            if is_return:
                raise exc.WrongReturnType(f'{data_type} nested inside {parent_variable_name}', type(data), position=f"{previous_index} in {parent_data_type}")
            else:
                raise exc.WrongParameterType(func_name, f"Nested variable in {parent_variable_name}", type(data), data_type, position=f"{previous_index} in {parent_data_type}")

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
                hints, return_type = TypeEnforcer.__generate_hints_dict(concat_args, func)
                defaults: list = []

                for key in hints.keys():
                    if type(hints[key]) == types.GenericAlias and not recursive:
                        hints[key] = hints[key].__origin__
                    elif type(hints[key]) == types.GenericAlias and hints[key].__origin__ not in TypeEnforcer.__allowed_for_recursive_checking:
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
                TypeEnforcer.__check_args({'return':return_type}, {'return':return_value}, func, recursive=recursive, return_check=True)
                return return_value
            return inner
        return enforcement


if __name__ == "__main__":
    class Silly:
        pass

    class Doof(Silly):
        pass

    @TypeEnforcer.enforcer(recursive=True)
    def foo(n, t: tuple[int, str] | dict[int,str], h: dict[str,int] | int, v: typing.Callable, f: list[str, int], x: typing.Any, y: str, z: typing.Optional[bool]=True, a: str="hello") -> list[str]:
        return ["hi"]

    class zeug:
        @TypeEnforcer.enforcer(recursive=True)
        def __init__(self, x: tuple[int, str]):
            pass

        @TypeEnforcer.enforcer(recursive=True)
        def ziggle(self, x: dict) -> tuple[str, int, str, tuple[int, str]] | dict[str,str]:
            return {"":""}#("he", 1, "ho", (1, "2"))

    def zoo():
        pass

    x = foo(Doof(), (2,"hi"), 1 , zoo, ['r', 1], 1, "hi", z=None)
    print(x)

    z = zeug((1, ""))
    z.ziggle({1:2})
