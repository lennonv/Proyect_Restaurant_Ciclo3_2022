FROM python:3.6.15

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5000

ENTRYPOINT ["python3"]
CMD ["app.py"] 