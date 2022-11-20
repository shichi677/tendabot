FROM python:3.10.7

RUN apt update
RUN apt install -y \
    locales \
    ffmpeg \
    cmake \
    build-essential
RUN locale-gen ja_JP.UTF-8

ENV TZ Asia/Tokyo
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

# RUN dd if=/dev/zero of=/swapfile bs=1M count=1024
# RUN chmod 600 /swapfile
# RUN mkswap /swapfile
# RUN swapon /swapfile
# RUN swapon -s
RUN fallocate -l 1024M swapfile
RUN chmod 0600 swapfile
RUN mkswap swapfile
# RUN echo 10 > /proc/sys/vm/swappiness
RUN swapon swapfile

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

RUN git clone -b 0.13.2 https://github.com/VOICEVOX/voicevox_core.git
WORKDIR /code/voicevox_core

RUN curl -s -OL https://github.com/microsoft/onnxruntime/releases/download/v1.10.0/onnxruntime-linux-x64-1.10.0.tgz && \
    tar -xzvf onnxruntime-linux-x64-1.10.0.tgz && \
    mv onnxruntime-linux-x64-1.10.0/ onnxruntime/ && \
    mkdir ./core/lib && \
    cp -r onnxruntime/lib ./core && \
    rm onnxruntime-linux-x64-1.10.0.tgz

RUN curl -s -OL https://github.com/VOICEVOX/voicevox_core/releases/download/0.13.2/voicevox_core-linux-x64-cpu-0.13.2.zip && \
    unzip -q voicevox_core-linux-x64-cpu-0.13.2.zip && \
    rm voicevox_core-linux-x64-cpu-0.13.2.zip && \
    mv voicevox_core-linux-x64-cpu-0.13.2/libcore.so voicevox_core-linux-x64-cpu-0.13.2/core.h ./core/lib/.

RUN pip install -r requirements.txt
RUN pip install .
RUN curl -s -OL https://jaist.dl.sourceforge.net/project/open-jtalk/Dictionary/open_jtalk_dic-1.11/open_jtalk_dic_utf_8-1.11.tar.gz && \
    tar -xzvf open_jtalk_dic_utf_8-1.11.tar.gz && \
    mv open_jtalk_dic_utf_8-1.11 ../ 

WORKDIR /code
RUN rm -rf voicevox_core
CMD python discordbot.py