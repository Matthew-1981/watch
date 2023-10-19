
import sys
from pathlib import Path
import datetime as dt

from connector import WatchDB
from interpolation.collection import LinearInterpolation


def smart_prompt(wait=10, add=0):
    """Returns the next instance where seconds are //wait as a datetime obj"""
    time = dt.datetime.now() + dt.timedelta(seconds=add)
    nex = dt.timedelta(seconds=wait + (time.second // wait * wait + wait) - time.second)
    return (time + nex).replace(microsecond=0)


def smart_measure(prompt, datetime):
    """Returns the difference between prompt and datetime"""
    return (prompt - datetime).total_seconds()


def smart_cycle(wait=10, add=0):
    """Returns time difference between the system watch and another watch"""
    prompt = smart_prompt(wait, add)
    input(f'press ENTER at {prompt.time()} ')
    return round(smart_measure(prompt, dt.datetime.now()), 1)


def shorten_list(initial_list):
    if len(initial_list) == 0:
        return "Null"

    out = []
    left = initial_list[0]
    right = initial_list[0]

    for i in range(1, len(initial_list)):

        if initial_list[i] - 1 == right:
            right = initial_list[i]
        else:
            if left == right:
                out.append(str(left))
            else:
                out.append(f"{left}-{right}")

            left = initial_list[i]
            right = initial_list[i]

    if left == right:
        out.append(str(left))
    else:
        out.append(f"{left}-{right}")

    return ', '.join(out)


def configure_default_watch(db: WatchDB, watch_id: int) -> None:
    tmp = db.con.execute("""SELECT name FROM sqlite_master WHERE type='table'
                            AND name='def_watch'""").fetchall()
    if not tmp:
        db.con.execute('CREATE TABLE def_watch (watch_id INT PRIMARY KEY)')
    db.con.execute('DELETE FROM def_watch')
    db.con.execute('INSERT INTO def_watch VALUES (?)', (watch_id,))
    db.con.commit()


def get_default_watch(db: WatchDB) -> int:
    tmp = db.con.execute("SELECT watch_id FROM def_watch").fetchall()
    if len(tmp) > 1:
        raise ValueError("More than one entry in def_watch")
    return tmp[0][0]


def main():
    import prettytable as pt
    INTERPOLATION_METHOD = LinearInterpolation

    print("watchDB - watch measurement database")

    working_dir = Path(__file__).parent
    if len(sys.argv) <= 1:
        database_name = working_dir / 'watchDB.sqlite3'
    else:
        database_name = Path(sys.argv[1])
    database = WatchDB(str(database_name))

    try:
        default_watch = get_default_watch(database)
        database.change_watch(default_watch)
    except Exception:
        print("Default watch is not configured.")

    while True:
        inp = input(f"{database.get_watch_name()}> ")

        try:
            match inp.split():

                case ["change", "default", integer]:
                    try:
                        configure_default_watch(database, int(integer))
                    except Exception as e:
                        print(f"Could not change default due to error:\n{e}")
                    else:
                        print(f"default changed to {integer}")

                case ["watches"]:
                    titles = ('watch id', 'name', 'date', 'cycles no.', 'measures no.')
                    dat = database.database_info()
                    table = pt.PrettyTable(titles)
                    table.add_rows(dat)
                    print(table)

                case ["change", "watch", *watch_id]:
                    watch_id = ' '.join(watch_id)
                    try:
                        watch_id = int(watch_id)
                    except Exception:
                        pass
                    try:
                        database.change_watch(watch_id)
                    except Exception:
                        print(f'Error: watch {watch_id} does not exist')
                    else:
                        print(f'Watch changed to {watch_id}')

                case ["change", "cycle", cycle]:
                    try:
                        cycle = int(cycle)
                        database.change_cycle(cycle)
                    except Exception:
                        print(f'Error: cycle {cycle} does not exist')
                    else:
                        print(f'Cycle changed to {cycle}')

                case ["add", "watch", *name]:
                    try:
                        name = ' '.join(name)
                        database.add_watch(name)
                    except Exception:
                        print('Error: Unable to add watch')
                    else:
                        print(f'Added watch {name}')

                case ["new", "cycle"]:
                    database.new_cycle()

                case ["measure"]:
                    cursor = database.con.execute(
                        '''
                        SELECT measure
                        FROM logs
                        WHERE watch_id = ?
                        AND cycle = ?
                        ORDER BY timedate DESC
                        ''',
                        (database.watch, database.cycle)
                    )
                    temp = cursor.fetchall()
                    if len(temp) == 0:
                        key = 0
                    else:
                        key = temp[0][0]
                    time = smart_cycle(add=key)
                    inp = None
                    while inp not in ['y', 'n']:
                        inp = input(f'add measure {time}? [y/n] ')
                    if inp == 'y':
                        database.add_measure(time)
                        print('Measure added')
                    else:
                        print('Measure not added')

                case ["manual", "measure", measure]:
                    measure = round(float(measure), 1)
                    database.add_measure(measure)

                case ["del", "watch"]:
                    prompt = None
                    while prompt not in ['y', 'n']:
                        prompt = input(f'Delete watch {database.get_watch_name()}? [y/n] ')
                    if prompt == 'y':
                        try:
                            database.del_current_watch()
                        except Exception:
                            print('Error: Unable to delete watch')
                        else:
                            print(f'watch deleted')

                case ["del", "cycle"]:
                    prompt = None
                    while prompt not in ['y', 'n']:
                        prompt = input(f'Delete cycle {database.cycle}? [y/n] ')
                    if prompt == 'y':
                        try:
                            tmp = database.cycle
                            database.del_current_cycle()
                        except Exception:
                            print('Error: Unable to delete cycle')
                        else:
                            print(f'cycle {tmp} deleted')

                case ["del", "measure", measure]:
                    prompt = None
                    while prompt not in ['y', 'n']:
                        prompt = input(f'Delete measure {measure}? [y/n] ')
                    if prompt == 'y':
                        try:
                            database.del_measure(int(measure))
                        except Exception:
                            print(f'Error: Measure {measure} does not exist')
                        else:
                            print(f'measure {measure} deleted')

                case ["log"]:
                    try:
                        data = database.data.difference()
                    except Exception:
                        print("Unable to produce log.")
                    else:
                        table = pt.PrettyTable(('log id', 'timedate', 'measure', 'difference'))
                        table.add_rows(reversed(data))
                        print(str(table))

                case ["fill"]:
                    try:
                        data = database.data.fill(INTERPOLATION_METHOD)
                    except Exception:
                        print("Unable to produce filled log.")
                    else:
                        table = pt.PrettyTable(('timedate', 'measure', 'difference'))
                        table.add_rows(reversed([(a, b, c) for _, a, b, c in data]))
                        print(str(table))

                case ["stat"]:
                    try:
                        data = database.data.stats(INTERPOLATION_METHOD)
                    except Exception:
                        print("Unable to produce stats.")
                    else:
                        table = pt.PrettyTable(('Average', 'Delta', 'Median'))
                        table.add_row((data['average'],
                                       data['delta'],
                                       data['median']))
                        print(str(table))

                case ["current"]:
                    cursor = database.con.execute(
                        'SELECT DISTINCT cycle FROM logs WHERE watch_id = ?',
                        (database.watch,)
                    )
                    data = [w[0] for w in cursor.fetchall()]
                    cycles = shorten_list(data)
                    table = pt.PrettyTable(('watch id', 'name', 'current cycle', 'all cycles'))
                    table.add_row((database.watch, database.get_watch_name(), database.cycle, cycles))
                    print(str(table))

                case ["SQL"]:
                    print('Entering SQL editor...')
                    code = input('SQL> ')
                    try:
                        cursor = database.con.execute(code)
                    except Exception as e:
                        print(e)
                    else:
                        data = cursor.fetchall()
                        if data:
                            table = pt.PrettyTable()
                            table.add_rows(data)
                            print(table)

                case ["exit"]:
                    database.close()
                    exit(0)

                case []:
                    pass

                case _:
                    print("Error: Invalid input")

        except Exception as e:
            print(f"FATAL ERROR: '{e}'")


if __name__ == "__main__":
    main()
