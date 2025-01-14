from tabulate import tabulate

from .fastcmd import CommandApp
from .facade import Manager
from . import utils

app = CommandApp()
manager = Manager('tmp', 'tmp', 'tmp', 30)


@app.command('swap_watch', 'sw', description='Change current watch')
def change_watch(name: str):
    utils.run_with_handling(manager.change_watch, name)


@app.command('swap_cycle', 'sc', description='Change current cycle')
def change_cycle(cycle: int):
    utils.run_with_handling(manager.change_cycle, cycle)


@app.command('add_watch', 'aw', description="Add a new watch")
def add_watch(name: str):
    utils.run_with_handling(manager.add_watch, name)


@app.command('add_cycle', 'ac', description="Add a new cycle")
def add_cycle():
    utils.run_with_handling(manager.add_cycle)


@app.command('add_log', 'al', description='Add a new measure to the current cycle')
def add_log():
    measure = utils.smart_cycle()
    utils.run_with_handling(manager.add_log, measure)


@app.command('list_watches', 'lw', description='List all watches')
def list_watches():
    def print_watches(watches):
        table = tabulate([[w.name, w.cycles] for w in watches], headers=['Name', 'Cycles'], tablefmt='grid')
        print(table)
    utils.run_with_handling(manager.get_watch_list, on_success=print_watches)


@app.command('list_logs', 'll', description='List all logs for the current watch and cycle')
def list_logs():
    def print_logs(logs):
        table = tabulate([[l.time, l.measure] for l in logs], headers=['Time', 'Measure'], tablefmt='grid')
        print(table)
    utils.run_with_handling(manager.get_log_list, on_success=print_logs)


@app.command('log_stats', 'ls', description='Get statistics for the current watch and cycle')
def log_stats():
    def print_stats(stats):
        table = tabulate(stats.items(), headers=['Statistic', 'Value'], tablefmt='grid')
        print(table)
    utils.run_with_handling(manager.get_log_stats, on_success=print_stats)


@app.command('delete_watch', 'dw', description='Delete a watch')
def delete_watch(name: str):
    utils.run_with_handling(manager.delete_watch, name)


@app.command('delete_log', 'dl', description='Delete a log entry')
def delete_log(log_id: int):
    utils.run_with_handling(manager.delete_log, log_id)


@app.command('delete_cycle', 'dc', description='Delete a cycle')
def delete_cycle(cycle_id: int):
    utils.run_with_handling(manager.delete_cycle, cycle_id)
