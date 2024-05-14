from mysql.connector.errors import IntegrityError
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import settings
from .data_manipulation.interpolation import LinearInterpolation
from .data_manipulation.log import WatchLogFrame
from .db_access import DBAccess
from .utils import convert_table

app = FastAPI()
db = DBAccess(settings.DATABASE_CONFIG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get('/watchlist')
async def watchlist(request: Request):
    async with db.access() as wp:
        await wp.cursor.execute('SELECT watch_id, name FROM info')
        watches = convert_table(('id', 'name'), await wp.cursor.fetchall())
        for watch in watches:
            await wp.cursor.execute('SELECT DISTINCT cycle FROM logs WHERE watch_id = %d',
                                    (watch['id'],))
            watch['cycles'] = [t[0] for t in await wp.cursor.fetchall()]
    return watches


class AddWatchRequest(BaseModel):
    name: str


@app.post('/watchlist')
async def add_watch(request: AddWatchRequest):
    async with db.access() as wp:
        try:
            await wp.cursor.execute('INSERT INTO info (name) VALUES (%s)', (request.name,))
        except IntegrityError:
            raise HTTPException(status_code=400, detail='Failed to insert.')
        else:
            await wp.commit()
    return {'status': 'ok'}


@app.delete('/watchlist/{watch_id}')
async def delete_watch(request: Request, watch_id: int):
    async with db.access() as wp:
        await wp.cursor.execute('DELETE FROM info WHERE watch_id = %d', (watch_id,))
        if wp.cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail='Watch not found.')
        await wp.cursor.execute('DELETE FROM logs WHERE watch_id = %d', (watch_id,))
        await wp.commit()
    return {'status': 'ok'}


@app.get('/measurements/{watch_id}/{cycle}')
async def measurements(request: Request, watch_id: int, cycle: int):
    async with db.access() as wp:
        await wp.cursor.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = %d AND cycle = %d
            ORDER BY timedate;
            ''',
            (watch_id, cycle)
        )
    frame = WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), wp.cursor.fetchall()).get_log_with_dif()
    return frame.data


@app.get('/stats/{watch_id}/{cycle}')
async def stats(request: Request, watch_id: int, cycle: int):
    async with db.access() as wp:
        await wp.cursor.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = %d AND cycle = %d
            ORDER BY timedate;
            ''',
            (watch_id, cycle)
        )
    table = wp.cursor.fetchall()
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
    async with db.access() as wp:
        await wp.cursor.execute('DELETE FROM logs WHERE log_id = %d', (log_id,))
        if wp.cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail='Log not found.')
        await wp.commit()
    return {'status': 'ok'}


class CreateMeasurementRequest(BaseModel):
    datetime: str
    measure: float


@app.post('/measurements/{watch_id}/{cycle}')
async def add_measurement(request: CreateMeasurementRequest, watch_id: int, cycle: int):
    async with db.access() as wp:
        try:
            await wp.cursor.execute(
                '''
                INSERT INTO logs (watch_id, cycle, timedate, measure)
                VALUES (?, ?, ?, ?);
                ''',
                (watch_id, cycle, request.datetime, request.measure)
            )
        except IntegrityError:
            raise HTTPException(status_code=400, detail='Failed to insert.')
        await wp.commit()
    return {'status': 'ok'}
