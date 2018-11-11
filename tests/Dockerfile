# Dockerfile for building an image able to run the test suite
FROM python:3.6-alpine

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "-m", "pytest"]
CMD ["-vv"]
WORKDIR /src
VOLUME ["/src", "/results"]