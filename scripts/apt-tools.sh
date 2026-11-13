#!/usr/bin/env sh
set -e
export DEBIAN_FRONTEND=noninteractive
NO="--no-recommends --no-suggests --no-conflicts --no-breaks --no-replaces --no-enhances"

apt-get update -qq
apt-get install -y -qq debtree > /dev/null 2>&1

rm /etc/apt/sources.list.d/ubuntu.sources
echo "deb http://archive.ubuntu.com/ubuntu noble main" > /etc/apt/sources.list
apt-get update -qq

for package in jq wget curl; do
    apt-cache depends --recurse $NO $package > /out/$package.txt
done
apt-cache rdepends $NO curl > /out/curl-rdepends.txt
debtree wget > /out/wget-debtree.dot 2> /dev/null
