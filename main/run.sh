#!/usr/bin/with-contenv bashio

bashio::log.info "Hello World!"
bashio::log.info "SSL Sync addon запущено"

# Keep the addon running
while true; do
    sleep 3600
done
