from ubuntu:jammy

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \ 
    python3-pip \ 
    python3-venv \ 
    libpq-dev \ 
    build-essential

# Create new user but not switching to it yet
RUN useradd -m appuser
COPY . /home/appuser/warning_system
WORKDIR /home/appuser/warning_system
RUN chown -R appuser:appuser /home/appuser/warning_system
RUN chmod +x entrypoint.sh
RUN python3 -m venv .venv
RUN /bin/bash -c "source .venv/bin/activate \
        && pip install --upgrade pip && \
        pip install -r requirements.txt"

# Switch to non-root user
USER appuser
ENTRYPOINT [ "entrypoint.sh" ]