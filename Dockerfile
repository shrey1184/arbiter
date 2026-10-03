FROM python:3.11-slim
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY ui ./ui
COPY config.yaml config.ollama-only.yaml ./
RUN pip install --no-cache-dir -e .
EXPOSE 8000 8501
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
