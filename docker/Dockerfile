# docker/Dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY ../requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ../src .

CMD ["fastapi", "run", "shuttledrop.py"]