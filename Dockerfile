FROM python:3.11-slim

RUN apt update && \
    apt install -y jq curl && \
    apt clean

COPY entrypoint.sh /entrypoint.sh
COPY fingerprint.py /fingerprint.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh", "/mods"]