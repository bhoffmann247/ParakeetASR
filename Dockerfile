FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3.10-dev python3-pip python3.10-venv libsndfile1 build-essential curl git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip, pin setuptools < 81 (82+ removed pkg_resources needed by pytorch-lightning 2.0.7)
RUN pip install --upgrade pip "setuptools<81"

# Install uWSGI
RUN pip install uwsgi

COPY ./requirements.txt requirements.txt

# Install Cython and youtokentome (youtokentome needs Cython at build time
# but pip's build isolation prevents it from seeing the global install)
RUN pip install Cython
RUN pip install youtokentome --no-build-isolation

# Install PyTorch 2.2.0 FIRST with CUDA 12.1 support
# Using 2.2.0 for device_mesh support required by NeMo
RUN pip install torch==2.2.0 torchaudio==2.2.0 torchvision==0.17.0 --index-url https://download.pytorch.org/whl/cu121

# Install requirements without allowing PyTorch downgrades
# Use constraints to lock PyTorch versions
RUN echo "torch==2.2.0" > /tmp/constraints.txt && \
    echo "torchaudio==2.2.0" >> /tmp/constraints.txt && \
    echo "torchvision==0.17.0" >> /tmp/constraints.txt && \
    echo "numpy<2" >> /tmp/constraints.txt && \
    echo "huggingface-hub<0.24" >> /tmp/constraints.txt && \
    echo "transformers<4.40" >> /tmp/constraints.txt && \
    echo "megatron-core==0.5.0" >> /tmp/constraints.txt && \
    pip install -r requirements.txt --constraint /tmp/constraints.txt

# Verify PyTorch version and NeMo import
RUN python3 -c "\
import torch; \
print(f'PyTorch version: {torch.__version__}'); \
from torch.distributed import device_mesh; \
print('device_mesh module found'); \
import nemo; \
print(f'NeMo version: {nemo.__version__}'); \
from nemo.collections.asr.models import EncDecRNNTBPEModel; \
print('NeMo ASR models imported successfully')"

RUN useradd --no-create-home nginx

COPY ./app .

COPY . .

CMD ["uwsgi","--ini","app.ini"]
