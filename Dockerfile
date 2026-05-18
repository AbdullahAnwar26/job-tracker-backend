FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libmagic1 \
    file \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD python manage.py collectstatic --noinput && \
    python manage.py migrate && \
    python manage.py spectacular --file schema.yml && \
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --log-level debug