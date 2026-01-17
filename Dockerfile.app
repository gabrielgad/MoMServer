# syntax=docker/dockerfile:1.4
# MoM Server Application Image
# Fast builds for Python/config changes (< 2 min)
#
# Build: ./scripts/build-app.sh --push
# Rebuild: On every code change (fast!)

ARG TGE_IMAGE=10.0.0.6:5000/momserver/tge-builder:v1.4
FROM ${TGE_IMAGE}

WORKDIR /server

# Copy application files (order by change frequency - least to most)
COPY common /server/common/
COPY mud_ext /server/mud_ext/
COPY projects /server/projects/
COPY serverconfig /server/serverconfig/
COPY mud /server/mud/
COPY *.py /server/
COPY main.cs /server/
COPY docker-entrypoint.sh /server/

# Create required directories
RUN mkdir -p data/master data/character logs && \
    chmod +x /server/docker-entrypoint.sh

# Ports:
# 2002-2003: Master server
# 7000-7001: World server
# 28000-28100: Zone servers
# 8192: Additional services
EXPOSE 2002 2003 7000 7001 28000-28100 8192

ENTRYPOINT ["/server/docker-entrypoint.sh"]
