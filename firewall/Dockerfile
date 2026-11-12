FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    nftables \
    iproute2 \
    iputils-ping \
    curl \
    tcpdump \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    nftables \
    iproute2 \
    iputils-ping \
    curl \
    tcpdump \
    procps \
    python3 \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]
