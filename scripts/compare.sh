#!/usr/bin/env sh
cd "$(dirname "$0")/.."
UBUNTU=http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz
mkdir -p examples/apt

our_edges() {
    ./run.sh --package "$1" --repo "$UBUNTU" --output "examples/$1.png" \
        | sed -n 's/^    "\(.*\)" -> "\(.*\)";$/\1 \2/p' | sort -u
}

apt_edges() {
    awk '/^[^ ]/ { name = $1; virtual = 0; next }
         /Depends: </ { virtual = 1; next }
         /Depends:/ { print name, $2; next }
         virtual { print name, $1; virtual = 0 }' "examples/apt/$1.txt" | sort -u
}

echo "===== штатные инструменты apt в контейнере Ubuntu 24.04 ====="
docker run --rm --platform linux/amd64 \
    -v "$PWD/scripts:/scripts:ro" -v "$PWD/examples/apt:/out" \
    ubuntu:24.04 sh /scripts/apt-tools.sh
dot -Tpng -o examples/apt/wget-debtree.png examples/apt/wget-debtree.dot
echo "готово: examples/apt/"

ours=$(mktemp)
theirs=$(mktemp)
for package in jq wget curl; do
    echo
    echo "===== $package: наш граф и apt-cache depends --recurse ====="
    our_edges "$package" > "$ours"
    apt_edges "$package" > "$theirs"
    echo "рёбер у нас: $(wc -l < "$ours" | tr -d " "), у apt-cache: $(wc -l < "$theirs" | tr -d " ")"
    diff "$ours" "$theirs" && echo "рёбра совпадают"
done
rm -f "$ours" "$theirs"

echo
echo "===== обратные зависимости curl: apt-cache rdepends ====="
cat examples/apt/curl-rdepends.txt
echo
echo "===== обратные зависимости curl: наша программа ====="
./run.sh --package curl --repo "$UBUNTU" --reverse \
    --output examples/curl-reverse.png | grep -e '->'
