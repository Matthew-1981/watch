FROM python:3.11-slim-buster

WORKDIR /backend
ADD . /backend
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80

CMD ["python", "./run.py"]
