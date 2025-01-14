from typing import Optional
from datetime import datetime, timedelta
from urllib import parse
import json

import requests
from communication import messages, responses


class FacadeError(Exception):
    pass


class FacadeRequestError(FacadeError):
    pass


class FacadeOperationalError(FacadeError):

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.resp_message = message
        super().__init__(f'status_code={self.status_code} message={self.resp_message}')


class WatchFacade:

    def __init__(self, url: str, default_token_expiration_minutes: int | None = None):
        self.url = parse.urlparse(url)
        self.token_expiration_minutes = default_token_expiration_minutes
        if self.url.path != '':
            raise ValueError('Path in the URL has to be empty.')

        self.register_user_path = '/register'
        self.login_user_path = '/login'
        self.logout_user_path = '/logout'
        self.refresh_user_path = '/refresh'
        self.terminate_user_path = '/terminate'

        self.watch_list_path = '/watch/list'
        self.watch_add_path = '/watch/add'
        self.watch_delete_path = '/watch/delete'

        self.log_list_path = '/logs/list'
        self.log_stats_path = '/logs/stats'
        self.log_delete_path = '/logs/delete'
        self.log_delete_cycle_path = '/logs/del_cycle'
        self.log_add_path = '/log/add'

    def _resolve_token_expiration(self, expiration_minutes: int | None) -> int:
        if expiration_minutes is not None:
            return expiration_minutes
        elif self.token_expiration_minutes is not None:
            return self.token_expiration_minutes
        else:
            raise ValueError('No default token_expiration_minutes configured.')

    def _send[T](
            self,
            path: str,
            message: messages.BaseMessage,
            return_type: type[T]
    ) -> T:
        try:
            resp = requests.post(str(self.url._replace(path=path)), json=message.model_dump())
        except requests.exceptions.RequestException as e:
            raise FacadeRequestError("Error while communicating with the backend.") from e
        if resp.status_code != 200:
            tmp = json.loads(resp.content)
            raise FacadeOperationalError(status_code=resp.status_code, message=tmp['detail'])
        return return_type.model_validate_json(resp.content)

    def register_user(self, user: str, password: str):
        message = messages.UserRegisterMessage(
            user_name=user,
            password=password
        )
        return self._send(self.register_user_path, message, responses.UserCreationResponse)

    def login_user(self,
                   user: str,
                   password: str,
                   token_expiration_minutes: Optional[int] = None
    ) -> responses.TokenResponse:
        message = messages.UserLoginMessage(
            user_name=user,
            password=password,
            expiration_minutes=self._resolve_token_expiration(token_expiration_minutes)
        )
        return self._send(self.login_user_path, message, responses.TokenResponse)

    def logout_user(self, token: str) -> responses.LogOutResponse:
        message = messages.LoggedInUserMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=10
            )
        )
        return self._send(self.logout_user_path, message, responses.LogOutResponse)

    def refresh_user(self, token: str, expiration_minutes: Optional[int] = None) -> responses.LoggedInResponse:
        message = messages.LoggedInUserMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            )
        )
        return self._send(self.refresh_user_path, message, responses.LoggedInResponse)

    def terminate_user(self, token: str) -> responses.LogOutResponse:
        message = messages.LoggedInUserMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=10
            )
        )
        return self._send(self.terminate_user_path, message, responses.LogOutResponse)

    def get_watch_list(self, token: str, expiration_minutes: Optional[int] = None) -> responses.WatchListResponse:
        message = messages.LoggedInUserMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            )
        )
        return self._send(self.watch_list_path, message, responses.WatchListResponse)

    def add_watch(self,
                  token: str,
                  watch_name: str,
                  expiration_minutes: Optional[int] = None
    ) -> responses.WatchEditResponse:
        message = messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            name=watch_name
        )
        return self._send(self.watch_add_path, message, responses.WatchEditResponse)

    def delete_watch(self,
                     token: str,
                     watch_name: str,
                     expiration_minutes: Optional[int] = None
    ) -> responses.WatchEditResponse:
        message = messages.EditWatchMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            name=watch_name
        )
        return self._send(self.watch_delete_path, message, responses.WatchEditResponse)

    def get_log_list(self,
                     token: str,
                     watch_name: str,
                     cycle: int,
                     expiration_minutes: Optional[int] = None
    ) -> responses.LogListResponse:
        message = messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            watch_name=watch_name,
            cycle=cycle
        )
        return self._send(self.log_list_path, message, responses.LogListResponse)

    def delete_cycle(self,
                     token: str,
                     watch_name: str,
                     cycle: int,
                     expiration_minutes: Optional[int] = None
    ) -> responses.LoggedInResponse:
        message = messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            watch_name=watch_name,
            cycle=cycle
        )
        return self._send(self.log_delete_cycle_path, message, responses.LoggedInResponse)

    def get_log_stats(self,
                      token: str,
                      watch_name: str,
                      cycle: int,
                      expiration_minutes: Optional[int] = None
    ) -> responses.StatsResponse:
        message = messages.SpecifyWatchDataMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            watch_name=watch_name,
            cycle=cycle
        )
        return self._send(self.log_stats_path, message, responses.StatsResponse)

    def delete_log(self,
                   token: str,
                   watch_name: str,
                   cycle: int,
                   log_id: int,
                   expiration_minutes: Optional[int] = None
    ) -> responses.LoggedInResponse:
        message = messages.SpecifyLogDataMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            watch_name=watch_name,
            cycle=cycle,
            log_id=log_id
        )
        return self._send(self.log_delete_path, message, responses.LoggedInResponse)

    def add_log(self,
                token: str,
                watch_name: str,
                cycle: int,
                time: datetime,
                measure: float,
                expiration_minutes: Optional[int] = None
    ) -> responses.LogAddedResponse:
        message = messages.CreateMeasurementMessage(
            auth=messages.AuthMessage(
                token=token,
                expiration_minutes=self._resolve_token_expiration(expiration_minutes)
            ),
            watch_name=watch_name,
            cycle=cycle,
            datetime=time,
            measure=measure
        )
        return self._send(self.log_add_path, message, responses.LogAddedResponse)


class ManagerError(FacadeError):
    pass


class ManagerOperationalError(ManagerError):
    pass


class ManagerNotLoggedInError(ManagerError):
    pass


class Manager:

    def __init__(self, url: str, user: str, password: str, token_expiration_minutes: int,
                 login_now: bool = True, auto_login: bool = False):
        self.user = user
        self.password = password
        self.default_expiration = token_expiration_minutes
        self.auto_login = auto_login
        self.facade = WatchFacade(url, self.default_expiration)

        self.token: str | None = None
        self.expiration: datetime | None = None

        self.watch: str | None = None
        self.cycle: int | None = None

        if login_now:
            self.login()

    def is_logged_in(self) -> bool:
        return (self.token is None
                and self.expiration is not None
                and self.expiration < datetime.now() + timedelta(seconds=5))

    def _check_login(self):
        if not self.is_logged_in():
            if self.auto_login:
                self.login()
            else:
                self.token = None
                self.expiration = None
                raise ManagerNotLoggedInError(f"User {self.user} not logged in.")

    def _resolve_watch(self, watch_name: str | None = None):
        watch = watch_name if watch_name is not None else self.watch
        if watch is None:
            raise ManagerOperationalError("Watch not specified.")
        return watch

    def _handle_logged_in_response(self, res: responses.LoggedInResponse):
        assert self.user == res.auth.user
        self.expiration = res.auth.expiration_date

    def add_user(self, name: str, password: str) -> responses.UserCreationResponse:
        return self.facade.register_user(name, password)

    def login(self):
        if not self.is_logged_in():
            ret = self.facade.login_user(self.user, self.password)
            self.token = ret.token
            self.expiration = ret.expiration_date
        else:
            ret = self.facade.refresh_user(self.token)
            self.expiration = ret.auth.expiration_date

    def logout(self):
        self._check_login()
        self.facade.logout_user(self.token)
        self.token = None
        self.expiration = None

    def terminate_user(self):
        self._check_login()
        self.facade.terminate_user(self.token)
        self.token = None
        self.expiration = None

    def get_watch_list(self) -> responses.WatchListResponse:
        self._check_login()
        resp = self.facade.get_watch_list(self.token)
        self._handle_logged_in_response(resp)
        return resp

    def add_watch(self, name: str) -> responses.WatchEditResponse:
        self._check_login()
        resp = self.facade.add_watch(self.token, name)
        self._handle_logged_in_response(resp)
        return resp

    def delete_watch(self, watch_name: str | None) -> responses.WatchEditResponse:
        watch = self._resolve_watch(watch_name)
        self._check_login()
        resp = self.facade.delete_watch(self.token, watch)
        self._handle_logged_in_response(resp)
        return resp

    def change_watch(self, name: str):
        self._check_login()
        watches = self.facade.get_watch_list(self.token)
        self._handle_logged_in_response(watches)
        for watch in watches.watches:
            if watch.name == name:
                cycles = watch.cycles
                break
        else:
            raise ManagerOperationalError(f"Watch with name {name} not found.")
        self.watch = name
        self.cycle = max(cycles)

    def change_cycle(self, cycle: int):
        self._resolve_watch()
        self._check_login()
        watches = self.facade.get_watch_list(self.token)
        self._handle_logged_in_response(watches)
        cycles = None
        for watch in watches.watches:
            if watch.name == self.watch:
                cycles = watch.cycles
                break
        assert cycles is not None
        if cycle not in cycles:
            raise ManagerOperationalError(f"Watch {self.watch} does not have a cycle {cycle}.")
        else:
            self.cycle = cycle

    def add_cycle(self):
        self._resolve_watch()
        self._check_login()
        watches = self.facade.get_watch_list(self.token)
        self._handle_logged_in_response(watches)
        cycles= None
        for watch in watches.watches:
            if watch.name == self.watch:
                cycles = watch.cycles
                break
        assert cycles is not None
        self.cycle = max(cycles) + 1

    def get_log_list(self) -> responses.LogListResponse:
        self._resolve_watch()
        self._check_login()
        resp = self.facade.get_log_list(self.token, self.watch, self.cycle)
        self._handle_logged_in_response(resp)
        return resp

    def get_log_stats(self) -> responses.StatsResponse:
        self._resolve_watch()
        self._check_login()
        resp = self.facade.get_log_stats(self.token, self.watch, self.cycle)
        self._handle_logged_in_response(resp)
        return resp

    def delete_log(self, log_id: int) -> responses.LoggedInResponse:
        self._resolve_watch()
        self._check_login()
        resp = self.facade.delete_log(self.token, self.watch, self.cycle, log_id)
        self._handle_logged_in_response(resp)
        return resp

    def delete_cycle(self) -> responses.LoggedInResponse:
        self._resolve_watch()
        self._check_login()
        resp = self.facade.delete_cycle(self.token, self.watch, self.cycle, self.expiration)
        self._handle_logged_in_response(resp)
        self.watch = None
        self.cycle = None
        return resp

    def add_log(self, measure: float, time: Optional[datetime] = None) -> responses.LogAddedResponse:
        self._resolve_watch()
        self._check_login()
        measure = round(measure, 2)
        time = time if time is not None else datetime.now()
        resp = self.facade.add_log(self.token, self.watch, self.cycle, time, measure)
        self._handle_logged_in_response(resp)
        return resp
