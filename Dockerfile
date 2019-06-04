FROM python:3.6

ENV PYTHONUNBUFFERED 1

COPY . /app
WORKDIR /app
RUN pip install .

CMD python -m bot.app
