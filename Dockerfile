FROM python:3.11-bookworm

ARG DEBIAN_FRONTEND=noninteractive

# Install essential system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl git build-essential ca-certificates \
    python3-venv python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Python venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements_streamlit.txt /app/requirements_streamlit.txt
RUN pip install --no-cache-dir -r /app/requirements_streamlit.txt

# Install Python dependencies
COPY requirements_streamlit.txt .
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copy application code
WORKDIR /app
COPY assets/ /app/assets/
COPY content/ /app/content/
COPY gdpr_consent/ /app/gdpr_consent
COPY src/ /app/src/
COPY app.py /app/app.py
COPY settings.json /app/settings.json
COPY default-parameters.json /app/default-parameters.json
COPY .streamlit/config.toml /app/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501
ENV PORT=8501

# Entrypoint
ENTRYPOINT ["/opt/venv/bin/streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]