FROM python:3.11-slim-buster

WORKDIR /watch
COPY ./backend ./backend
COPY ./communication ./communication
WORKDIR /watch/backend

RUN rm -r tests/  # just to be safe

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "27712"]
