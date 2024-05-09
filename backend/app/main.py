from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

import settings
from .utils import convert_table
from .db_access import DBAccess
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
            watch['cycles'] = conn.execute('SELECT DISTINCT cycle FROM logs WHERE watch_id = ?', (watch['id'],)).fetchall()
    return watches


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
