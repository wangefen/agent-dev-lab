FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


copy pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "agent_dev_lab.api.main:app", "--host", "0.0.0.0", "--port", "8000"]