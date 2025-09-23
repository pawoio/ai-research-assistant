FROM python:3.11-slim

# Use the container workspace variable
ARG WORKSPACE_PATH=/workspace/app
RUN mkdir -p ${WORKSPACE_PATH}
WORKDIR ${WORKSPACE_PATH}

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ${WORKSPACE_PATH}
