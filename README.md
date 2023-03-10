# Type Enforcer
add as a decorator to any python function to enforce type hints, turning python functions from dynamically to statically typed in the runtime.

Enforces python type hints. 
Parameters and returns that do not have explicit hints will be assumed to have types of typing.Any
Supports basic type hinting operations, like Type[], Union[], and GenericAlias objects like dict[] and list[]

Supports recursive type checking in runtime! If you want to check that the contents in a deep nested datastructure match type hints,
just enable recursive type checking with "recursive=True". Note that this significantly increases the computation necessary to run functions
so it is advisable to only run this during the debugging phase of development. Note that as of now this only works with lists, tuples, sets, and dicts

Overall, best used with debugging

## Install
1. pip install TypeEnforcer
2. from TypeEnforcer.TypeEnforcement.type_enforcer import TypeEnforcer
3. @TypeEnforcer.enforcer