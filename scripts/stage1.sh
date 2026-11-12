#!/usr/bin/env sh
cd "$(dirname "$0")/.."
URL=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz

run() {
    echo
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "код возврата: $?"
}

echo "===== корректные параметры ====="
run --package curl --repo "$URL" --version 8.5.0-2ubuntu10 --output curl.png
run --package A --repo repos/simple.txt --test

echo
echo "===== ошибки ====="
run --repo "$URL"
run --package curl
run --package "Curl!" --repo "$URL"
run --package curl --repo "ftp://example.org/Packages"
run --package curl --repo "not-a-url"
run --package a --repo repos/simple.txt --test
run --package A --repo repos/nope.txt --test
run --package curl --repo "$URL" --version abc
run --package curl --repo "$URL" --output graph.jpg
run --package curl --repo "$URL" --output nope/graph.png
