# Type Enforcer
Adds a decorator which can enforce basic python type hints.
Ensure that all of the function parameters have type hints! Even if it is just typing.Any
Supports basic type hinting operations, like Type[], Union[], and *Container*[*datatype*]

Must also use hints for the return type, following same rules as the parameters

good for debugging

## Install
1. pip install TypeEnforcer
2. from TypeEnforcer.TypeEnforcement.type_enforcer import TypeEnforcer
3. @TypeEnforcer.enforcer