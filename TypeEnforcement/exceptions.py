class WrongParameterType(TypeError):
    """
    Raise exception when a parameter of unexpected type is passed to a function
    """
    def __init__(self, function_name: str, parameter_name: str, received_type: str, expected_type: str, position=None):
        message = f"Function received the incorrect type {received_type} for the parameter {parameter_name} in the function {function_name}. Expected type {expected_type}"
        if position:
            message = f"At position {position} " + message 
        super().__init__(message)
        

class WrongReturnType(TypeError):
    """
    Raise exception when a function returns unexpected value
    """
    def __init__(self, expected_return_type: str, actual_return_type: str, func_name: str, position=None):
        message = f"Function {func_name} returned a {actual_return_type}, expected a(n) {expected_return_type}"
        if position:
            message = f"At position {position} " + message 
        super().__init__(message)