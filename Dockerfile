FROM python:3.13-slim

WORKDIR /app

# Install PyTorch CPU-only from the lightweight CPU index (no CUDA, ~200MB vs ~2GB)
RUN pip install --no-cache-dir --timeout 300 torch --index-url https://download.pytorch.org/whl/cpu

# Install project dependencies plus streamlit
COPY pyproject.toml .
RUN pip install --no-cache-dir . streamlit

# Install Cargo for the code assistant
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy application code
COPY . .

EXPOSE 8501
 
CMD ["streamlit", "run", "streamlit_app.py", "--server.headless", "true", "--server.address", "0.0.0.0"]
