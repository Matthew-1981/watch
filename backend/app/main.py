import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from fastapi import status

from communication import messages, responses
from . import settings, security, db, utils
from .data_manipulation.interpolation import LinearInterpolation
from .data_manipulation.log import WatchLogFrame

db_access = db.DBAccess(settings.DATABASE_CONFIG)
sec_functions = security.SecurityCreator(db_access)
token_daemon = db.DeleteTokenDaemonCreator(db_access, 5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    max_retries = 10
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            await db.db_initiate(db_access, *db.schema_files)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise e

    asyncio.create_task(token_daemon())
    yield

app = FastAPI(lifespan=lifespan)

@app.post('/register')
async def register_user(request: messages.UserRegisterMessage):
    user = await sec_functions.register_user(request)
    return responses.UserCreationResponse(
        user_name=user.data.user_name,
        creation_date=user.data.date_of_creation
    )


@app.post('/login')
async def login_user(request: messages.UserLoginMessage) -> responses.TokenResponse:
    _, token = await sec_functions.login_user(request)
    return responses.TokenResponse(
        token=token.data.token,
        expiration_date=token.data.expiration
    )


@app.post('/logout')
async def logout_user(
        request: messages.LoggedInUserMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LogOutResponse:
    async with db_access.access() as wp:
        await auth_bundle.token.delete(wp.cursor)
        await wp.commit()
    return responses.LogOutResponse(
        user=auth_bundle.user.data.user_name,
        token=auth_bundle.token.data.token
    )


@app.post('/refresh')
async def refresh_user(
        request: messages.LoggedInUserMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LoggedInResponse:
    return responses.LoggedInResponse(auth=utils.parse_auth_bundle(auth_bundle))


@app.post('/terminate')
async def terminate_user(
        request: messages.LoggedInUserMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LogOutResponse:
    async with db_access.access() as wp:
        await auth_bundle.user.delete(wp.cursor)
        await wp.commit()
    return responses.LogOutResponse(
        user=auth_bundle.user.data.user_name,
        token=auth_bundle.token.data.token
    )


@app.post('/watch/list')
async def watchlist(
        request: messages.LoggedInUserMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.WatchListResponse:
    async with db_access.access() as wp:
        watches = await db.WatchRecordManager(auth_bundle.user).get_all_watches(wp.cursor)
        out: list[responses.WatchElementResponse] = []
        for watch in watches:
            cycles = await db.LogRecordManager(watch).get_cycles(wp.cursor)
            out.append(responses.WatchElementResponse(
                name=watch.data.name,
                date_of_creation=watch.data.date_of_creation,
                cycles=cycles
            ))
    return responses.WatchListResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        watches=out
    )


@app.post('/watch/add')
async def add_watch(
        request: messages.EditWatchMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.WatchEditResponse:
    async with db_access.access() as wp:
        new_watch = db.NewWatch(
            user_id=auth_bundle.user.data.user_id,
            name=request.name,
            date_of_creation=datetime.now(timezone.utc)
        )
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).new_watch(wp.cursor, new_watch)
        except db.exceptions.ConstraintError:
            await wp.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Watch '{request.name}' already exists.")
        await wp.commit()
    return responses.WatchEditResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        name=watch.data.name,
        date_of_creation=watch.data.date_of_creation
    )


@app.post('/watch/delete')
async def delete_watch(
        request: messages.EditWatchMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.WatchEditResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.name)
        except db.exceptions.OperationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Watch {request.name} does not exits.")
        await watch.delete(wp.cursor)
        await wp.commit()
    return responses.WatchEditResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        name=watch.data.name,
        date_of_creation=watch.data.date_of_creation
    )


@app.post('/logs/list')
async def log_list(
        request: messages.SpecifyWatchDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LogListResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )
        logs = await db.LogRecordManager(watch).get_logs(wp.cursor, request.cycle)
    table = [(log.data.log_id, log.data.timedate, log.data.measure) for log in logs]
    frame = WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), table).get_log_with_dif()
    tmp = [
        responses.LogResponse(
            log_id=f.other['log_id'],
            time=f.datetime,
            measure=f.measure,
            difference=f.other['difference']
        ) for f in frame.data]
    return responses.LogListResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        logs=tmp
    )


@app.post('/logs/fill')
async def log_fill(
        request: messages.SpecifyWatchDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LogListResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )
        logs = await db.LogRecordManager(watch).get_logs(wp.cursor, request.cycle)
    table = [(log.data.log_id, log.data.timedate, log.data.measure) for log in logs]
    frame = (WatchLogFrame
             .from_table(('log_id', 'datetime', 'measure'), table)
             .fill(LinearInterpolation)
             .get_log_with_dif())
    tmp = [
        responses.LogResponse(
            log_id=None,
            time=f.datetime,
            measure=f.measure,
            difference=f.other['difference']
        ) for f in frame.data]
    return responses.LogListResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        logs=tmp
    )


@app.post('/logs/stats')
async def stats(
        request: messages.SpecifyWatchDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.StatsResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )
        logs = await db.LogRecordManager(watch).get_logs(wp.cursor, request.cycle)
    table = [(log.data.log_id, log.data.timedate, log.data.measure) for log in logs]
    frame = WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), table).fill(LinearInterpolation)
    try:
        out = responses.StatsResponse(
            auth=utils.parse_auth_bundle(auth_bundle),
            average=frame.average,
            deviation=frame.standard_deviation,
            delta=frame.delta
        )
    except ZeroDivisionError:
        out = responses.StatsResponse(
            auth=utils.parse_auth_bundle(auth_bundle),
            average=None,
            deviation=None,
            delta=None
        )
    return out


@app.post('/logs/delete')
async def delete_measurement(
        request: messages.SpecifyLogDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LoggedInResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )
        try:
            log = await db.LogRecordManager(watch).get_log_by_id(wp.cursor, request.cycle, request.log_id)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Log with id {request.log_id} does not exist in this cycle."
            )
        await log.delete(wp.cursor)
        await wp.commit()
    return responses.LoggedInResponse(auth=utils.parse_auth_bundle(auth_bundle))


@app.post('/logs/del_cycle')
async def delete_cycle(
        request: messages.SpecifyWatchDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LoggedInResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )

        try:
            await db.LogRecordManager(watch).delete_logs(wp.cursor, request.cycle)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No cycle {request.cycle} for watch {request.watch_name}."
            )
        await wp.commit()
    return responses.LoggedInResponse(auth=utils.parse_auth_bundle(auth_bundle))


@app.post('/logs/add')
async def add_measurement(
        request: messages.CreateMeasurementMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.LogAddedResponse:
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecordManager(auth_bundle.user).get_watch_by_name(wp.cursor, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch '{request.watch_name}' not found"
            )
        new_log = db.NewLog(
            watch_id=watch.data.watch_id,
            cycle=request.cycle,
            timedate=request.datetime.astimezone(timezone.utc)
                if request.datetime.tzinfo is None
                else request.datetime.replace(tzinfo=timezone.utc),
            measure=round(request.measure, 2)
        )
        log = await db.LogRecordManager(watch).new_log(wp.cursor, request.cycle, new_log)
        await wp.commit()
    return responses.LogAddedResponse(
        auth=utils.parse_auth_bundle(auth_bundle),
        log_id=log.data.log_id,
        time=log.data.timedate,
        measure=log.data.measure
    )
