FROM python:3.12-slim

RUN apt update && \
    apt install -y jq curl && \
    apt clean && \
    python3 -m pip install --no-cache-dir murmurhash2 requests

COPY src/ /

ENTRYPOINT ["python3", "/init.py", "/mods"]