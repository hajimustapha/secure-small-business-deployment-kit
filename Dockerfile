FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --no-create-home appuser

COPY app.py ./

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5050

CMD ["python", "app.py"]
