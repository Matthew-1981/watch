from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/login')
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get('/register')
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
