FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["sh", "-c", "gunicorn run_dev:app --bind 0.0.0.0:${PORT:-5002} --workers 2"]
