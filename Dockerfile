FROM python:3.12-slim

WORKDIR /app

# 安装依赖 (只有 requests，标准库已有 http.server)
RUN pip install --no-cache-dir requests==2.31.0

COPY sub_proxy.py .

EXPOSE 25500

ENV UPSTREAM_URL=""
ENV CUSTOM_UA="clash-verge/v2.5.3"
ENV PROXY_PORT=25500
ENV LOG_LEVEL=INFO

CMD ["python3", "sub_proxy.py"]
