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
    return [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
