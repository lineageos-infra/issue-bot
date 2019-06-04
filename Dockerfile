FROM python:3.6

COPY . /app
WORKDIR /app
RUN pip install .

CMD python -m bot.app
