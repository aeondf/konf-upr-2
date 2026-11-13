#!/usr/bin/env sh
cd "$(dirname "$0")/.."
UBUNTU=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
mkdir -p examples

run() {
    echo
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "код возврата: $?"
}

show() {
    echo
    echo "--- $1 ---"
    cat "$1"
}

echo "===== тестовый репозиторий ====="
show repos/complex.txt
run --package A --repo repos/complex.txt --test --output examples/complex.png
show repos/cycle.txt
run --package D --repo repos/cycle.txt --test --output examples/cycle.png
show repos/diamond.txt
run --package D --repo repos/diamond.txt --test --reverse --output examples/diamond-reverse.png

echo
echo "===== три пакета Ubuntu ====="
run --package jq --repo "$UBUNTU" --output examples/jq.png
run --package wget --repo "$UBUNTU" --output examples/wget.png
run --package curl --repo "$UBUNTU" --output examples/curl.png

echo
echo "===== обратные зависимости ====="
run --package curl --repo "$UBUNTU" --reverse --output examples/curl-reverse.png

echo
echo "===== ошибки ====="
run --package A --repo repos/simple.txt --test --output graph.svg
run --package A --repo repos/simple.txt --test --output nope/graph.png
