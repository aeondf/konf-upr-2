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

echo "===== обратные зависимости в тестовом репозитории ====="
show repos/diamond.txt
run --package D --repo repos/diamond.txt --test --reverse
run --package B --repo repos/diamond.txt --test --reverse
run --package A --repo repos/diamond.txt --test --reverse
show repos/cycle.txt
run --package A --repo repos/cycle.txt --test --reverse
show repos/complex.txt
run --package H --repo repos/complex.txt --test --reverse
run --package Z --repo repos/complex.txt --test --reverse

echo
echo "===== сравнение: прямые и обратные зависимости одного пакета ====="
run --package C --repo repos/complex.txt --test
run --package C --repo repos/complex.txt --test --reverse

echo
echo "===== ошибки ====="
run --package X --repo repos/diamond.txt --test --reverse

echo
echo "===== настоящий репозиторий Ubuntu ====="
run --package curl --repo "$UBUNTU" --reverse
