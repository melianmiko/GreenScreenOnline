FROM ubuntu:jammy

RUN DEBIAN_FRONTEND=noninteractive apt update  \
 && apt install -y --no-install-recommends ffmpeg python3 python3-pip \
 && rm -rf /var/lib/{apt,dpkg,cache,log}/

WORKDIR /root

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./ /root/
ENV PYTHONPATH=/root
CMD ["gunicorn", "-b 0.0.0.0:8000", "app:app"]
