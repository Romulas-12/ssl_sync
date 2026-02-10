ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip \
    && python3 -m pip install --no-cache-dir paramiko scp pyopenssl

# Copy files
COPY run.sh /
COPY main.py /app/
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
