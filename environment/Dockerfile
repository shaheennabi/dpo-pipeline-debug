FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl bash nodejs npm && \
    npm install -g @openai/codex@latest

WORKDIR /solution
COPY instruction.md /solution/instruction.md
COPY README.md /solution/README.md
COPY data/ /solution/data/
COPY src/ /solution/src/
CMD ["bash"]