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

# Install PyTorch 2.2.0 FIRST with CUDA 12.1 support
# Using 2.2.0 for device_mesh support required by NeMo
RUN pip install torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0 --index-url https://download.pytorch.org/whl/cu121

# Install requirements without allowing PyTorch downgrades
# Use constraints to lock PyTorch versions
RUN echo "torch==2.2.0" > /tmp/constraints.txt && \
    echo "torchaudio==2.2.0" >> /tmp/constraints.txt && \
    echo "torchvision==0.17.0" >> /tmp/constraints.txt && \
    pip install -r requirements.txt --constraint /tmp/constraints.txt

# Verify PyTorch version and device_mesh availability
RUN python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); from torch.distributed import device_mesh; print('device_mesh module found')"

RUN useradd --no-create-home nginx

COPY ./app .

COPY . .

CMD ["uwsgi","--ini","app.ini"]
