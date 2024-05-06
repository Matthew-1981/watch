from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()


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
def test(request: Request):
    return [{'id': 1, 'name': 'test', 'cycles': [1, 2, 3]}, {'id': 2, 'name': 'test2', 'cycles': [4, 5, 6]}]


@app.get('/watch/{id}/{cycle}/measurements')
def measurements(request: Request, id: int, cycle: int):
    xd = 12 if id == 1 else 13
    return [{'id': 0, 'datetime': '2021-01-01 12:00:00', 'value': 1.0, 'diff': None},
            {'id': 1, 'datetime': '2021-01-01 12:00:01', 'value': xd, 'diff': 0.1}]