# Use NVIDIA's official NeMo container which has all dependencies
# pre-installed and tested (PyTorch, CUDA, NeMo, torchaudio, etc.)
# NeMo 25.02 = NeMo 2.2.0, PyTorch 2.6, required for parakeet-tdt-0.6b-v2
FROM nvcr.io/nvidia/nemo:25.02

WORKDIR /app

# Install web server and Flask dependencies (not included in NeMo container)
RUN pip install uwsgi flask flask-expects-json flask-Cors pydub ffmpeg-python jiwer

# Install ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --no-create-home nginx

COPY ./app .

COPY . .

CMD ["uwsgi","--ini","app.ini"]
