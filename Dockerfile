FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code/

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . /code/

RUN chmod +x /code/entrypoint.sh

USER appuser

EXPOSE 8000

CMD ["sh", "/code_playon/entrypoint.sh"]