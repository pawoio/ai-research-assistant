FROM python:3.11-slim

# Use the container workspace variable
ARG WORKSPACE_PATH=/workspace/app
RUN mkdir -p ${WORKSPACE_PATH}
WORKDIR ${WORKSPACE_PATH}

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install unzip, which is needed to extract tflint
RUN apt-get update && apt-get install -y unzip

# Install tflint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

COPY . ${WORKSPACE_PATH}
