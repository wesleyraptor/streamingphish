# Base image and deps.
FROM ubuntu:16.04
RUN apt-get update; apt-get -y upgrade
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip

# Install Jupyter.
RUN pip3 install jupyterlab

# Install preqeqs for content in Jupyter notebook.
ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Add files.
ADD jupyter_notebook_config.py /jupyter_notebook_config.py

# Expose the port for Jupyter notebook.
EXPOSE 9000

# Start service.
WORKDIR /opt/streamingphish/notebooks/
ENTRYPOINT ["/usr/local/bin/jupyter", "lab", "--config=/jupyter_notebook_config.py"]
