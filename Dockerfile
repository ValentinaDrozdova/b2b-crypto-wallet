FROM python:3.12-alpine

# install postgres headers
RUN apk update && apk add --no-cache postgresql-dev

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./b2b_crypto_wallet /app
WORKDIR /app

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]