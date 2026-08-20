FROM python:3.11-slim
WORKDIR /tests
COPY test.sh /tests/test.sh
COPY grader.py /tests/grader.py
COPY src/ /tests/src/
COPY data/ /tests/data/
COPY hidden_preferences.jsonl /tests/hidden_preferences.jsonl
RUN sed -i 's/\r$//' /tests/test.sh
RUN chmod +x /tests/test.sh
CMD ["bash", "/tests/test.sh"]
