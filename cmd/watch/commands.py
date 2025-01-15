from pathlib import Path
import getpass

from tabulate import tabulate
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

from communication import responses
from .fastcmd import CommandApp, CommandError
from .facade import Manager, FacadeError
from . import utils, config

config_file = Path('~/.watchrc').expanduser()

def setup_config(file: Path) -> config.ConfigContents:
    if not file.exists():
        print('Config file not found creating one now...')
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
        with open(file, 'w') as f:
            f.write(contents.model_dump_json(indent=4))
        return contents

    else:
        with open(file, 'r') as f:
            contents = config.ConfigContents.model_validate_json(f.read())
        return contents


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
            measure_val = utils.smart_cycle()
            if utils.uy_prompt(f"Add measure {measure_val} to '{manager.watch}' cycle {manager.cycle}?"):
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
        if utils.uy_prompt(f"Are you sure you want to delete watch '{name}'?"):
            utils.run_with_handling(manager.delete_watch, name)

    @app.command('del-log', 'dl', description='Delete a log entry')
    def delete_log(log_id: int):
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.delete_log, log_id)

    @app.command('del-cycle', 'dc', description='Delete a cycle')
    def delete_cycle():
        if not utils.check_watch_chosen(manager):
            return
        utils.run_with_handling(manager.delete_cycle)

    @app.command('help', description="Display commands with their description")
    def help_():
        print(app.get_str_description())

    return app


def main():
    settings = setup_config(config_file)
    manager = Manager(
        url=settings.config_server.host,
        user=settings.config_user.username,
        password=settings.config_user.password,
        token_expiration_minutes=settings.config_server.token_expiration_minutes,
        login_now=True,
        auto_login=True
    )
    app = get_app(manager)

    completer = WordCompleter(list(app.aliases.keys()) + ['exit'])
    session = PromptSession(completer=completer)

    if settings.default_watch is not None:
        try:
            manager.change_watch(settings.default_watch)
        except FacadeError as e:
            print(e)

    while True:
        try:
            current_watch = manager.watch if manager.watch is not None else ''
            user_input = session.prompt(f'{current_watch}> ')
        except (KeyboardInterrupt, EOFError):
            break

        if user_input is None:
            pass
        else:
            if user_input.strip() == 'exit':
                assert isinstance(user_input, str)
                manager.logout()
                break
        try:
            app(user_input)
        except CommandError as e:
            print(e)
