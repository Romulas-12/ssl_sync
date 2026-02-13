ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip \
    && python3 -m pip install --no-cache-dir paramiko scp pyopenssl cryptography

# Copy files
COPY run.sh /
COPY main.py /app/
RUN chmod a+x /run.sh

ENTRYPOINT [ "/init" ]
CMD [ "/run.sh" ]
