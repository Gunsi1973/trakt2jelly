# Schlankes Python 3.14 Image als Basis
FROM python:3.14-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten (falls nötig, hier aktuell nicht)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Zuerst nur requirements kopieren für besseres Caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den restlichen Code kopieren
COPY . .

# Verzeichnisse für Volumes erstellen (Zustand und Logs)
RUN mkdir -p /app/logs /app/data

# Standard-Befehl: Führt den Sync aus
CMD ["python", "main.py"]