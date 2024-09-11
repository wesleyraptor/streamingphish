# Build from python3.9 base image.
FROM python:3.9

# Fix issue with setuptools.
RUN pip install setuptools==45

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