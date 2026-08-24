FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends clang make && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY orchestrator ./orchestrator
CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
