# Headless SCONE (sconecmd) with the OpenSim 3.3 backend.
# The official SCONE builds are Windows/Linux/macOS desktop apps. The Linux
# build is amd64 only, so on Apple silicon this image runs under emulation.
FROM --platform=linux/amd64 ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends liblapack3 libpng16-16 zlib1g libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY vendor/scone_amd64.deb /tmp/scone.deb
RUN dpkg-deb -x /tmp/scone.deb / && rm /tmp/scone.deb

ENV LD_LIBRARY_PATH=/opt/scone/lib:/opt/scone/bin
WORKDIR /work
ENTRYPOINT ["/opt/scone/bin/sconecmd"]
