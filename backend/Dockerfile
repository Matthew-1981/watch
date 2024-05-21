FROM python:3.11-slim-buster

ENV SERVER_HOST 0.0.0.0
ENV SERVER_PORT 80

WORKDIR /backend
ADD . /backend
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80

CMD ["python", "./run.py"]
