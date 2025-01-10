from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi import status
from mysql.connector.errors import IntegrityError
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from . import settings, security, messages, responses, db
from .data_manipulation.interpolation import LinearInterpolation
from .data_manipulation.log import WatchLogFrame

app = FastAPI()
db_access = db.DBAccess(settings.DATABASE_CONFIG)
sec_functions = security.SecurityCreator(db_access)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post('/register')
async def register_user(request: messages.UserRegisterMessage):
    user = await sec_functions.register_user(request)
    return responses.UserCreationResponse(
        user_name=user.data.user_name,
        creation_date=user.data.date_of_creation
    )


@app.post('/login')
async def user_login(request: messages.UserLoginMessage) -> responses.TokenResponse:
    _, token = await sec_functions.login_user(request)
    return responses.TokenResponse(
        token=token.data.token,
        expiration_date=token.data.expiration
    )


@app.get('/watch/list')
async def watchlist(
        request: messages.UserLoginMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
) -> responses.WatchListResponse:
    async with db_access.access() as wp:
        watches = await db.WatchRecord.get_all_watches(wp.cursor, auth_bundle.user)
        out: list[responses.WatchElementResponse]
        for watch in watches:
            cycles = await db.LogRecord.get_cycles(wp.cursor, watch.data.watch_id)
            out.append(responses.WatchElementResponse(
                name=watch.data.name,
                date_of_creation=watch.data.date_of_creation,
                cycles=cycles
            ))
    return responses.WatchListResponse(
        auth=responses.AuthResponse.parse(auth_bundle),
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
            date_of_creation=datetime.now()
        )
        try:
            watch = await db.WatchRecord.new_watch(wp.cursor, new_watch)
        except db.exceptions.ConstraintError:
            await wp.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Watch '{request.name}' already exists.")
        await wp.commit()
    return responses.WatchEditResponse(
        auth=responses.AuthResponse.parse(auth_bundle),
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
            watch = await db.WatchRecord.get_watch_by_name(wp.cursor, auth_bundle.user.data.user_id, request.name)
        except db.exceptions.OperationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Watch {request.name} does not exits.")
        await watch.delete(wp.cursor)
        await wp.commit()
    return responses.WatchEditResponse(
        auth=responses.AuthResponse.parse(auth_bundle),
        name=watch.data.name,
        date_of_creation=watch.data.date_of_creation
    )


@app.get('/logs/list')
async def log_list(
        request: messages.SpecifyWatchDataMessage,
        auth_bundle: security.AuthBundle = Depends(sec_functions.get_user)
):
    async with db_access.access() as wp:
        try:
            watch = await db.WatchRecord.get_watch_by_name(wp.cursor, auth_bundle.user.data.user_id, request.watch_name)
        except db.exceptions.OperationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watch {request.watch_name} not found."
            )
        logs = await db.LogRecord.get_logs(wp.cursor, watch.data.watch_id, request.cycle)
    table = [(log.data.log_id, log.data.timedate, log.data.measure) for log in logs]
    frame = WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), table).get_log_with_dif()
    return frame.data


@app.get('/stats/{watch_id}/{cycle}')
async def stats(request: Request, watch_id: int, cycle: int):
    async with db_access.access() as wp:
        await wp.cursor.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = %s AND cycle = %s
            ORDER BY timedate;
            ''',
            (watch_id, cycle)
        )
        table = await wp.cursor.fetchall()
    frame = (WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), table)
             .fill(LinearInterpolation))
    try:
        out = {
            'average': frame.average,
            'deviation': frame.standard_deviation,
            'delta': frame.delta
        }
    except ZeroDivisionError:
        out = {
            'average': 'N/A',
            'deviation': 'N/A',
            'delta': 0
        }
    return out


@app.delete('/measurements/{log_id}')
async def delete_measurement(request: Request, log_id: int):
    async with db_access.access() as wp:
        await wp.cursor.execute('DELETE FROM logs WHERE log_id = %s', (log_id,))
        if wp.cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail='Log not found.')
        await wp.commit()
    return {'status': 'ok'}


class CreateMeasurementRequest(BaseModel):
    datetime: str
    measure: float


@app.post('/measurements/{watch_id}/{cycle}')
async def add_measurement(request: CreateMeasurementRequest, watch_id: int, cycle: int):
    async with db_access.access() as wp:
        try:
            await wp.cursor.execute(
                '''
                INSERT INTO logs (watch_id, cycle, timedate, measure)
                VALUES (%s, %s, %s, %s);
                ''',
                (watch_id, cycle, request.datetime, request.measure)
            )
        except IntegrityError:
            raise HTTPException(status_code=400, detail='Failed to insert.')
        await wp.commit()
    return {'status': 'ok'}
