FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgdal-dev \
    libgeos-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user src/ .

ENV PORT=7860
ENV FLASK_DEBUG=false

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "run:app"]
