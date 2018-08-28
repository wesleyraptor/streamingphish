# Build from base image and install prereqs from repo.
FROM ubuntu:16.04
RUN apt-get update; apt-get -y upgrade
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip setuptools

# Install framework requirements.
ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Make project directories in /opt/streamingphish and copy framework files.
ADD config/config.yaml /opt/streamingphish/config/

# Temporarily add streamingphish source.
ADD streamingphish/ /tmp/source/
WORKDIR /tmp/source/

# Run unit tests.
RUN find . -name '*.pyc' -delete
RUN pytest -s --cov-report term-missing --cov=streamingphish

# Install.
RUN python3 setup.py install
RUN rm -rf /tmp/source

# Small hack, lots of debate in docker compose forums for how to address this.
# I only want service available on demand - not as a daemon during initialization.
WORKDIR /opt/streamingphish/
ENTRYPOINT ["sh", "-c", "sleep infinity"]
