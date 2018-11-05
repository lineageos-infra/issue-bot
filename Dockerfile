FROM python:3.6

COPY . /app
WORKDIR /app
RUN pip install gunicorn
RUN pip install .

RUN python test.py

CMD gunicorn -b 0.0.0.0:8080 bot.app:app
