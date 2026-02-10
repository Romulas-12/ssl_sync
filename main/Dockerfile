ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python
RUN apk add --no-cache python3
RUN pip install --no-cache-dir paramiko
RUN pip install --no-cache-dir scp
RUN pip install --no-cache-dir pyopenssl

# Copy files
COPY run.sh /
COPY main.py /app/
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
