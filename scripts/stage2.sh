#!/usr/bin/env sh
cd "$(dirname "$0")/.."
UBUNTU=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
DOCKER=https://download.docker.com/linux/ubuntu/dists/noble/stable/binary-amd64/Packages

run() {
    echo
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "код возврата: $?"
}

echo "===== прямые зависимости из репозитория Ubuntu ====="
run --package curl --repo "$UBUNTU"
run --package curl --repo "$UBUNTU" --version 8.5.0-2ubuntu10
run --package python3 --repo "$UBUNTU"

echo
echo "===== разные версии одного пакета: зависимости отличаются ====="
run --package docker-ce --repo "$DOCKER" --version "5:26.0.0-1~ubuntu.24.04~noble"
run --package docker-ce --repo "$DOCKER"

echo
echo "===== ошибки ====="
run --package curl --repo "$UBUNTU" --version 1.0
run --package no-such-package --repo "$UBUNTU"
run --package curl --repo http://archive.ubuntu.com/ubuntu/dists/noble/main/nope/Packages.gz
run --package curl --repo http://no-such-host.invalid/Packages
