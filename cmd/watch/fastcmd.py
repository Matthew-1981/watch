import inspect
import shlex
from typing import get_type_hints, get_origin, get_args, Any, Callable, Optional
from types import FunctionType


class FastCmdError(Exception):
    pass

class CommandError(FastCmdError):
    pass

class NoCommandError(CommandError):
    pass

class CommandDefinitionError(FastCmdError):
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
                raise CommandDefinitionError("The list must be the final input.")
            annotation = annotations.get(name, str)
            if annotation in self.atomic_types:
                inputs.append((name, annotation))
            else:
                origins = get_origin(annotation)
                arguments = get_args(annotation)
                if origins != list:
                    raise CommandDefinitionError("Only str, int, float, bool or list[<all former>] allowed.")
                if len(arguments) != 1:
                    raise CommandDefinitionError("List has to have exactly one atomic type specified.")
                inner_type = arguments[0]
                inputs.append((name, (origins, inner_type)))
                found_list = True

        self.func = func
        self.inputs = inputs

    def parse_args(self, args: list[str]) -> list:
        final_args: list = []

        arg_iter = iter(args)
        for name, type_ in self.inputs:

            if isinstance(type_, type):
                try:
                    current_value = next(arg_iter)
                except StopIteration:
                    raise CommandError("Not enough arguments")
                try:
                    final_value = type_(current_value)
                except ValueError:
                    raise CommandError(f"Wrong type for argument {name} - {current_value}"
                                       f" has to be convertable to {type_.__name__}")
                final_args.append(final_value)
            else:
                type1, type2 = type_
                assert type1 == list
                final_value = []
                for current_value in arg_iter:
                    try:
                        final_value.append(type2(current_value))
                    except ValueError:
                        raise CommandError(f"Wrong type for argument {name} - {current_value}"
                                           f" has to be convertable to {type_.__name__}")
                final_args.append(final_value)
                break

        return final_args

    def __call__(self, args: list[str]) -> Any:
        args = self.parse_args(args)
        return self.func(*args)


class CommandApp:

    def __init__(self):
        self.commands: dict[str, Command] = {}
        self.aliases: dict[str, str] = {}
        self.descriptions: dict[str, str] = {}

    def command(self, *names: str, description: Optional[str] = None) -> Callable[[FunctionType], FunctionType]:

        if len(names) == 0:
            raise CommandDefinitionError("No names for command specified.")

        def wrapper(func: FunctionType):
            command = Command(func)
            iter_names = iter(names)
            main_name = next(iter_names)

            self.commands[main_name] = command
            self.aliases[main_name] = main_name
            self.descriptions[main_name] = description

            while True:
                try:
                    name = next(iter_names)
                except StopIteration:
                    break
                if name in self.aliases:
                    raise CommandDefinitionError(f"Command with name {name} already added.")
                self.aliases[name] = main_name

            return func

        return wrapper

    def get_description(self) -> list[tuple[str, tuple[str, ...], str]]:
        out = []
        for command in self.commands.keys():
            aliases = tuple(filter(lambda x: self.aliases[x] == command and not x == command, self.aliases.keys()))
            out.append((command, aliases, self.descriptions[command]))
        return out

    def get_str_description(self) -> str:
        out = []
        for command, aliases, description in self.get_description():
            types = self.commands[command].inputs
            desc = f"\n{description}" if description is not None else ''
            aliases_message = f" or {aliases}" if len(aliases) > 0 else ''
            args = ' '.join(
                f'{type_.__name__}[{name}]' if isinstance(type_, type) else f'list[{type_[1].__name__}[{name}]]'
                for name, type_ in types)
            tmp = f'{command}{aliases_message}\nusage: {command} {args}{desc}'
            out.append(tmp)
        return '\n\n'.join(out)

    def run_parsed(self, name: str, args: list[str]) -> Any:
        if name not in self.aliases:
            raise CommandError(f"Command {name} not found.")
        main_name = self.aliases[name]
        return self.commands[main_name](args)

    def run_from_string(self, command: str) -> Any:
        try:
            arguments = shlex.split(command)
        except ValueError as e:
            raise CommandError("Invalid command format.") from e
        if len(arguments) == 0:
            raise NoCommandError("No command specified.")
        cmd = arguments[0]
        args = arguments[1:]
        return self.run_parsed(cmd, args)

    def __call__(self, command: str) -> Any:
        return self.run_from_string(command)
