from typing import Any, Callable
from datetime import datetime, timedelta
import traceback

from . import facade
from . import fastcmd


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
        print(e.resp_message)
    except facade.FacadeRequestError:
        traceback.print_exc()
    except fastcmd.CommandError as e:
        print(e)
    else:
        on_success(out)
