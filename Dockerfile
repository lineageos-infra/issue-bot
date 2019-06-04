FROM python:3.6

COPY . /app
WORKDIR /app
RUN pip install .

CMD python bot/app.py
