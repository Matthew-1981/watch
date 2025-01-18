import json
from pathlib import Path
import argparse
import getpass

from tabulate import tabulate
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from communication import responses
from .fastcmd import CommandApp, CommandError
from .facade import WatchFacade, Manager, FacadeOperationalError, ManagerOperationalError, FacadeRequestError
from . import utils, config


def create_config(file: Path, no_write: bool = False) -> config.ConfigContents:
    if not no_write:
        print('Creating configuration file...')
    else:
        print('Enter configuration information...')
    host = input('host: ')
    user_name = input('username: ')
    password = getpass.getpass(prompt='password: ')
    contents = config.ConfigContents(
        config_server=config.ConfigServer(
            host=host,
            token_expiration_minutes=10
        ),
        config_user=config.ConfigUser(
            username=user_name,
            password=password
        ),
        default_watch=None
    )
    if not no_write:
        with open(file, 'w') as f:
            f.write(contents.model_dump_json(indent=4))
    return contents


def get_config(file: Path) -> config.ConfigContents:
    if not file.exists():
        return create_config(file)
    else:
        with open(file, 'r') as f:
            return config.ConfigContents.model_validate_json(f.read())


def get_app(manager: Manager) -> CommandApp:
    app = CommandApp()

    @app.command('swap-watch', 'sw', description='Change current watch')
    def change_watch(name: str):
        utils.run_with_handling(manager.change_watch, name)

    @app.command('swap-cycle', 'sc', description='Change current cycle')
    def change_cycle(cycle: int):
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.change_cycle, cycle)

    @app.command('add-watch', 'aw', description="Add a new watch")
    def add_watch(name: str):
        utils.run_with_handling(manager.add_watch, name)

    @app.command('add-cycle', 'ac', description="Add a new cycle")
    def add_cycle():
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.add_cycle)

    @app.command('measure', 'm', description='Add a new measure to the current cycle')
    def add_log(measure: list[float]):
        if len(measure) > 1:
            print("Only one measure can be added at a time.")
            return
        if not utils.check_watch_chosen(manager):
            return

        if len(measure) == 0:
            logs = manager.get_log_fill()
            key = logs.logs[-1].measure if len(logs.logs) > 0 else 0.0
            measure_val = utils.smart_cycle(add=key)
            if utils.yn_prompt(f"Add measure {measure_val} to '{manager.watch}' cycle {manager.cycle}?"):
                utils.run_with_handling(manager.add_log, measure_val)
        else:
            measure_val = measure[0]
            utils.run_with_handling(manager.add_log, measure_val)

    @app.command('watches', 'lw', description='List all watches')
    def list_watches():
        def print_watches(watches: responses.WatchListResponse):
            table = [[w.name, w.date_of_creation, utils.parse_cycle_list(w.cycles)] for w in watches.watches]
            table = tabulate(table, headers=['Name', 'Creation date', 'Cycles'], tablefmt='grid')
            print(table)
        utils.run_with_handling(manager.get_watch_list, on_success=print_watches)

    @app.command('current', 'cur', description="Show current watch and cycle.")
    def current():
        if manager.watch is not None:
            table = tabulate([[manager.watch, manager.cycle]], ['Watch', 'Cycle'], tablefmt='grid')
            print(table)
        else:
            print("No watch selected.")

    @app.command('log', 'll', description='List all logs for the current watch and cycle')
    def list_logs():
        if not utils.check_watch_chosen(manager):
            return
        def print_logs(logs: responses.LogListResponse):
            table = [[l.log_id, l.time, l.measure, l.difference] for l in logs.logs]
            table = tabulate(table, headers=['Log ID', 'time', 'measure', 'difference'], tablefmt='grid')
            print(table)
        utils.run_with_handling(manager.get_log_list, on_success=print_logs)

    @app.command('fill', 'f', description='Show interpolated current log')
    def fill_logs():
        if not utils.check_watch_chosen(manager):
            return
        def print_logs(logs: responses.LogListResponse):
            table = [[l.time, l.measure, l.difference] for l in logs.logs]
            table = tabulate(table, headers=['time', 'measure', 'difference'], tablefmt='grid')
            print(table)
        utils.run_with_handling(manager.get_log_fill, on_success=print_logs)

    @app.command('stats', 'ls', description='Get statistics for the current watch and cycle')
    def log_stats():
        if not utils.check_watch_chosen(manager):
            return
        def print_stats(stats: responses.StatsResponse):
            table = [['average', stats.average], ['Deviation', stats.deviation], ['Delta', stats.delta]]
            table = tabulate(table, headers=['Statistic', 'Value'], tablefmt='grid')
            print(table)
        utils.run_with_handling(manager.get_log_stats, on_success=print_stats)

    @app.command('del-watch', 'dw', description='Delete a watch')
    def delete_watch(name: str):
        if utils.yn_prompt(f"Are you sure you want to delete watch '{name}'?"):
            utils.run_with_handling(manager.delete_watch, name)

    @app.command('del-log', 'dl', description='Delete a log entry')
    def delete_log(log_id: int):
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.delete_log, log_id)

    @app.command('del-cycle', 'dc', description='Delete the current cycle')
    def delete_cycle():
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.delete_cycle)

    @app.command('help', description="Display commands with their description")
    def help_():
        print(app.get_str_description())

    return app


def run_interactive(manager: Manager, app: CommandApp):
    completer = WordCompleter(list(app.aliases.keys()) + ['exit'])
    session = PromptSession(completer=completer)

    while True:
        try:
            current_watch = manager.watch if manager.watch is not None else ''
            user_input = session.prompt(f'{current_watch}> ')
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.strip() == '':
            continue
        elif user_input.strip() == 'exit':
            break
        else:
            try:
                app(user_input)
            except CommandError as e:
                print(e)


config_file = Path('~/.watchrc').expanduser()

def main():
    parser = argparse.ArgumentParser(description="Command line tool")
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('register', help='Register a new user')

    subparsers.add_parser('config', help='Change configuration')

    subparsers.add_parser('terminate', help='Terminate user')

    def_parser = subparsers.add_parser('default', help='Set default watch')
    def_parser.add_argument('name', type=str, help='Name of the new default watch')

    run_parser = subparsers.add_parser('run', help='Run the application with arguments')
    run_parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments for the run command')

    args = parser.parse_args()

    if args.command == 'register':
        settings = create_config(config_file)
        facade = WatchFacade(
            url=settings.config_server.host,
            default_token_expiration_minutes=settings.config_server.token_expiration_minutes
        )
        try:
            facade.register_user(settings.config_user.username, settings.config_user.password)
        except FacadeOperationalError as e:
            print(json.loads(e.resp_message)['detail'])
            exit(1)
        else:
            exit(0)
    elif args.command == 'config':
        create_config(config_file)
        exit(0)
    elif args.command == 'default':
        settings = get_config(config_file)
        settings.default_watch = args.name
        with open(config_file, 'w') as f:
            f.write(settings.model_dump_json(indent=4))
        exit(0)
    elif args.command == 'terminate':
        settings = create_config(config_file, no_write=True)
        if not utils.yn_prompt(f"Are you sure you want to delete user '{settings.config_user.username}'?"
                               f"(THIS OPERATION IS NOT REVERSIBLE!)"):
            exit(0)
        facade = WatchFacade(
            url=settings.config_server.host,
            default_token_expiration_minutes=settings.config_server.token_expiration_minutes
        )
        try:
            token = facade.login_user(settings.config_user.username, settings.config_user.password)
            facade.terminate_user(token.token)
        except FacadeOperationalError as e:
            print(e.resp_message)
            exit(1)
        else:
            exit(0)
    else:
        settings = get_config(config_file)
        manager = Manager(
            url=settings.config_server.host,
            user=settings.config_user.username,
            password=settings.config_user.password,
            token_expiration_minutes=settings.config_server.token_expiration_minutes,
            login_now=False,
            auto_login=True
        )
        try:
            manager.login()
        except FacadeOperationalError as e:
            detail = json.loads(e.resp_message)['detail']
            print(f"Failed to log in! (check config in {config_file})\ndetails: {detail}")
            exit(1)
        except FacadeRequestError as e:
            print(f"Cannot connect to the server! (check config in {config_file})\ndetails: {e}")
            exit(1)

        if settings.default_watch is not None:
            try:
                manager.change_watch(settings.default_watch)
            except ManagerOperationalError as e:
                print(e)

        app = get_app(manager)

        if args.command == 'run':
            if len(args.args) == 0:
                try:
                    app.run_parsed('watches', [])
                except CommandError as e:
                    print(e)
            else:
                name = args.args[0]
                if name.strip() in ['swap-watch', 'sw', 'swap-cycle', 'sc', 'add-cycle', 'ac']:
                    print(f"Command '{name.strip()}' is only allowed in interactive mode")
                    exit(1)
                arguments = args.args[1:]
                try:
                    app.run_parsed( name, arguments)
                except CommandError as e:
                    print(e)
        else:
            run_interactive(manager, app)

        manager.logout()
