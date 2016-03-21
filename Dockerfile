FROM python
MAINTAINER think@hotmail.de

RUN pip install --no-cache-dir pyaml

COPY bin /bin
COPY compose_plantuml /usr/local/lib/python3.5/site-packages/compose_plantuml
COPY ["features/*.feature", "Dockerfile", "README.md", "/"]

RUN chmod +x /bin/compose_plantuml

ENTRYPOINT ["python3", "/bin/compose_plantuml"]
