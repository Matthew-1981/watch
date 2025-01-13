import inspect
import shlex
from typing import get_type_hints, get_origin, get_args, Any, Callable
from types import FunctionType


class CommandError(Exception):
    pass

class NoCommandError(CommandError):
    pass

class CommandTypeError(CommandError):
    pass


class Command:

    atomic_types = str, int, float, bool

    def __init__(self, func: FunctionType):
        signature = inspect.signature(func)
        names = [name for name, _ in signature.parameters.items()]
        annotations = get_type_hints(func)

        inputs: list[tuple[str, type | tuple[type[list], type]]] = []
        found_list = False
        for name in names:
            if found_list:
                raise CommandTypeError("The list must be the final input.")
            annotation = annotations.get(name, str)
            if annotation in self.atomic_types:
                inputs.append((name, annotation))
            else:
                origins = get_origin(annotation)
                arguments = get_args(annotation)
                if origins != list:
                    raise CommandTypeError("Only str, int, float, bool or list[<all former>] allowed.")
                if len(arguments) != 1:
                    raise CommandTypeError("List has to have exactly one atomic type specified.")
                inner_type = arguments[0]
                inputs.append((name, (origins, inner_type)))
                found_list = True

        self.func = func
        self.inputs = inputs

    def parse_args(self, args: list[str]) -> list:
        i = 0
        inputs_iter = iter(self.inputs)
        final_args: list = []
        while i < len(args):
            current_value = args[i]
            name, type_ = next(inputs_iter)

            if isinstance(type_, type):
                final_value = type_(current_value)
                i += 1
                final_args.append(final_value)
            else:
                type1, type2 = type_
                assert type1 == list
                final_value = []
                i += 1
                while i < len(args):
                    final_value.append(type2(args[i]))
                    i += 1
                final_args.append(final_value)
                break
        try:
            next(inputs_iter)
        except StopIteration:
            pass
        else:
            raise CommandError("Not all arguments specified.")
        return final_args

    def __call__(self, args: list[str]) -> Any:
        args = self.parse_args(args)
        return self.func(*args)


class CommandApp:

    def __init__(self):
        self.commands: dict[str, Command] = {}

    def command(self, name: str) -> Callable[[FunctionType], FunctionType]:

        def wrapper(func: FunctionType):
            command = Command(func)
            if name in self.commands:
                raise CommandTypeError(f"Command with name {name} already added.")
            self.commands[name] = command
            return func

        return wrapper

    def run_command(self, name: str, args: list[str]) -> Any:
        if name not in self.commands:
            raise CommandError(f"Command {name} not found.")
        return self.commands[name](args)

    def parse_and_run(self, command: str) -> Any:
        arguments = shlex.split(command)
        if len(arguments) == 0:
            raise NoCommandError("No command specified.")
        cmd = arguments[0]
        args = arguments[1:]
        return self.run_command(cmd, args)

    def __call__(self, command: str) -> Any:
        return self.parse_and_run(command)
