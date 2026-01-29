FROM python:3.12-slim

COPY requirements.txt /
RUN apt update && \
    apt install -y jq curl && \
    apt clean && \
    python3 -m pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt

COPY src/ /app

ENTRYPOINT ["python3", "/app/init.py", "/mods"]