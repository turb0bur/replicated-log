FROM python:3.12-slim

WORKDIR /app

COPY secondary/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY secondary/secondary.py .
COPY common ./common/

RUN useradd -m appuser
USER appuser

EXPOSE 8000

ENTRYPOINT ["uvicorn", "secondary:app", "--host", "0.0.0.0"]
CMD ["--port", "8000"]
