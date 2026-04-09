# app/deploy/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY app/ app/
COPY data/upstream/ data/upstream/
COPY data/frameworks/ data/frameworks/
COPY results/ results/
COPY THIRD_PARTY_NOTICES.md .

EXPOSE 8050

CMD ["python", "-m", "app.dash_app.app"]
