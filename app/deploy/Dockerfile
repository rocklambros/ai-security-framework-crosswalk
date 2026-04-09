FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements-app.txt /app/
RUN pip install --no-cache-dir -r requirements-app.txt

# Copy application code
COPY app/ /app/app/
COPY classifier/ /app/classifier/
COPY mapping_engine/ /app/mapping_engine/
COPY data/ /app/data/
COPY runs/ /app/runs/
COPY results/ /app/results/

# CC BY-SA 4.0 attribution bundle
COPY app/deploy/THIRD_PARTY_NOTICES.md /app/attribution/THIRD_PARTY_NOTICES.md

# Copy config
COPY app/deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 7860

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
