FROM node:24-bookworm-slim AS tree
WORKDIR /build/tree
COPY tree/package.json tree/package-lock.json ./
COPY tree/simple/package.json simple/package.json
RUN npm ci --ignore-scripts
COPY tree/ ./
RUN npm run build:all

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY arborsynapse.py ./
COPY scripts/ scripts/
COPY server/ server/
COPY excel/ excel/
COPY --from=tree /build/tree/dist tree/dist
COPY --from=tree /build/tree/simple/dist tree/simple/dist
COPY --from=tree /build/tree/local-package tree/local-package
RUN python -c "import sys; sys.path.insert(0,'server'); import studentdash.config"
ENV ARBOR_DEMO=1 ARBOR_TEST_HOSTS=atlas STUDENTDASH_WORKBOOK=/app/data/classroom.xlsx STUDENTDASH_OUTPUT=/app/output
EXPOSE 5080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5080/health', timeout=3)"
CMD ["python", "scripts/run.py", "--prepared", "--no-browser", "--host", "0.0.0.0", "--port", "5080"]
