# Install on ubuntu.
FROM ubuntu:16.04
RUN apt-get update; apt-get -y upgrade
RUN apt-get install -y mongodb mongodb-server

# Create default data directory.
RUN mkdir -p /data/db

# Expose the default port.
EXPOSE 27017

# Start service when container runs.
ENTRYPOINT ["/usr/bin/mongod"]
