FROM python:3.13-slim

LABEL authors="bahodir"

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8006

ENTRYPOINT ["/app/entrypoint.sh"]
