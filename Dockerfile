FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -f /etc/nginx/sites-enabled/default && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chmod +x start.sh

EXPOSE 80

CMD ["./start.sh"]