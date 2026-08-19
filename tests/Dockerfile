FROM python:3.11-slim
# Verifier image should expose /tests as the test root expected by Harbor
WORKDIR /tests
# Copy only verifier-related files into /tests (build context is tests/)
COPY test.sh /tests/test.sh
COPY grader.py /tests/grader.py
COPY src/ /tests/src/
COPY data/ /tests/data/
COPY hidden_preferences.jsonl /tests/hidden_preferences.jsonl
# Normalize line endings in test.sh (Windows -> Unix) to avoid /usr/bin/env bash\r errors
RUN sed -i 's/\r$//' /tests/test.sh
# Install minimal deps if needed (none required beyond base python)
RUN chmod +x /tests/test.sh
CMD ["bash", "/tests/test.sh"]
