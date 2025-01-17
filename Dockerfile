FROM python:3-slim

WORKDIR /todofrog

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    postgresql-client \
    postgresql-server-dev-all \
    && rm -rf /var/lib/apt/lists/*

COPY . /todofrog

RUN python -m pip install -r requirements.txt

CMD python main.py
