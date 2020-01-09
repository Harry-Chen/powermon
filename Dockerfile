FROM python:buster

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple influxdb
CMD ["python3", "/srv/powermon/powermon.py"]

