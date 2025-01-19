from typing import Callable
from datetime import datetime, timedelta
import json

from pydantic import ValidationError

from . import facade


def smart_prompt(wait=10, add=0):
    time = datetime.now() + timedelta(seconds=add)
    nex = timedelta(seconds=wait + (time.second // wait * wait + wait) - time.second)
    return (time + nex).replace(microsecond=0)


def smart_measure(prompt, time):
    return (prompt - time).total_seconds()


def smart_cycle(wait=10, add=0):
    prompt = smart_prompt(wait, add)
    input(f'press ENTER at {prompt.time()} ')
    return round(smart_measure(prompt, datetime.now()), 1)


def parse_cycle_list(initial_list: list[int]) -> str:
    if len(initial_list) == 0:
        return 'No cycles'

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


def run_with_handling[T](func: Callable[..., T],
                         *args,
                         on_success: Callable[[T], None] = lambda x: None,
                         **kwargs
):
    try:
        out = func(*args, **kwargs)
    except facade.ManagerNotLoggedInError:
        print("The user is not logged in!")
        exit(1)
    except facade.ManagerOperationalError as e:
        print(e)
    except facade.FacadeOperationalError as e:
        print(json.loads(e.resp_message)['detail'])
    except ValidationError as e:
        print(e)
    else:
        on_success(out)


def yn_prompt(message: str) -> bool:
    print(message)
    answer = None
    while answer is None or answer not in ['yes', 'y', 'no', 'n']:
        answer = input('[yes, no]> ')
    return answer in ['yes', 'y']


def check_watch_chosen(manager: facade.Manager) -> bool:
    if manager.watch is None:
        print("This operation can only be done if a watch is specified.")
    return manager.watch is not None
