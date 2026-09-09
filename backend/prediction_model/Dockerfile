# EEQS-RAG 水文预测模拟模型镜像
# 构建:  docker build -t eeqs-prediction-model:latest .
FROM python:3.11-slim

WORKDIR /app
COPY model.py /app/model.py

# 约定：从 /io/input/ 读取输入文件，把结果写到 /io/output/
ENTRYPOINT ["python", "/app/model.py"]
