from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import settings
from .db_access import DBAccess
from .utils import convert_table
from .watch.log import WatchLogFrame

app = FastAPI()
db = DBAccess(settings.DATABASE_PATH)

origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get('/watchlist')
async def watchlist(request: Request):
    async with db.access() as conn:
        watches = conn.execute('SELECT watch_id, name FROM info').fetchall()
        watches = convert_table(('id', 'name'), watches)
        for watch in watches:
            watch['cycles'] = conn.execute('SELECT DISTINCT cycle FROM logs WHERE watch_id = ?',
                                           (watch['id'],)).fetchall()
    return watches


class AddWatchRequest(BaseModel):
    name: str


@app.post('/watchlist')
async def add_watch(request: AddWatchRequest):
    async with db.access() as conn:
        out = conn.execute('INSERT INTO info (name) VALUES (?)', (request.name,))
        if out.rowcount == 0:
            raise HTTPException(status_code=400, detail='Failed to insert.')
        conn.commit()
    return {'status': 'ok'}


@app.get('/measurements/{watch_id}/{cycle}')
async def measurements(request: Request, watch_id: int, cycle: int):
    async with db.access() as conn:
        table = conn.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = ? AND cycle = ?
            ORDER BY timedate;
            ''',
            (watch_id, cycle)
        ).fetchall()
    frame = WatchLogFrame.from_table(('log_id', 'datetime', 'measure'), table).get_log_with_dif()
    return frame.data


@app.delete('/measurements/{log_id}')
async def delete_measurement(request: Request, log_id: int):
    async with db.access() as conn:
        out = conn.execute('DELETE FROM logs WHERE log_id = ?', (log_id,))
        if out.rowcount == 0:
            raise HTTPException(status_code=400, detail='Log not found.')
        conn.commit()
    return {'status': 'ok'}


class CreateMeasurementRequest(BaseModel):
    datetime: str
    measure: float


@app.post('/measurements/{watch_id}/{cycle}')
async def add_measurement(request: CreateMeasurementRequest, watch_id: int, cycle: int):
    async with db.access() as conn:
        out = conn.execute(
            '''
            INSERT INTO logs (watch_id, cycle, timedate, measure)
            VALUES (?, ?, ?, ?);
            ''',
            (watch_id, cycle, request.datetime, request.measure)
        )
        if out.rowcount == 0:
            raise HTTPException(status_code=400, detail='Failed to insert.')
        conn.commit()
    return {'status': 'ok'}
