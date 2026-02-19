FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04 AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3.10-dev python3-pip python3.10-venv libsndfile1 build-essential curl git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uwsgi
RUN pip install ffmpeg-python

# Install compatible PyTorch versions FIRST with CUDA support
RUN pip install torch==2.1.0 torchaudio==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

RUN pip install numpy==1.26.4

COPY ./requirements.txt requirements.txt

# Install requirements without upgrading torch/torchaudio
RUN pip install -r requirements.txt --upgrade-strategy only-if-needed

RUN apt-get update

RUN useradd --no-create-home nginx

RUN pip install --upgrade pip

COPY ./app .

COPY . .

CMD ["uwsgi","--ini","app.ini"]
