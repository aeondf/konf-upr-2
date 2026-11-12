#!/usr/bin/env sh
cd "$(dirname "$0")/.."
UBUNTU=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz

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
show repos/simple.txt
run --package A --repo repos/simple.txt --test
show repos/diamond.txt
run --package A --repo repos/diamond.txt --test
show repos/cycle.txt
run --package A --repo repos/cycle.txt --test
run --package D --repo repos/cycle.txt --test
show repos/self.txt
run --package A --repo repos/self.txt --test
show repos/complex.txt
run --package A --repo repos/complex.txt --test
run --package Z --repo repos/complex.txt --test

echo
echo "===== ошибки тестового репозитория ====="
show repos/broken.txt
run --package A --repo repos/broken.txt --test
run --package A --repo repos/empty.txt --test
run --package X --repo repos/simple.txt --test

echo
echo "===== настоящий репозиторий Ubuntu ====="
run --package curl --repo "$UBUNTU"
