FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3.10-dev python3-pip python3.10-venv libsndfile1 build-essential curl git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip first
RUN pip install --upgrade pip

# Install uWSGI
RUN pip install uwsgi

COPY ./requirements.txt requirements.txt

# Install requirements first (this will install a PyTorch version)
RUN pip install -r requirements.txt

# Force reinstall PyTorch 2.2.0 with CUDA 12.1 support AFTER requirements
# This ensures device_mesh module is available and nothing downgrades it
RUN pip install --force-reinstall --no-deps torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0 --index-url https://download.pytorch.org/whl/cu121

RUN useradd --no-create-home nginx

COPY ./app .

COPY . .

CMD ["uwsgi","--ini","app.ini"]
