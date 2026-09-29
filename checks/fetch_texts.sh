#!/bin/zsh
# Download the public-domain running-key candidates into data/running_keys/ (gitignored).
set -e
cd ${0:A:h}/../data && mkdir -p running_keys && cd running_keys
get() { curl -sfL --max-time 180 -A 'kryptos-research/0.1' -o "$1" "$2" && echo "$1 $(wc -c < $1) bytes"; }
get carter_vol1.txt      https://archive.org/download/tomboftutankhame01cart/tomboftutankhame01cart_djvu.txt
get carter_vol2.txt      https://archive.org/download/tomboftutankhame02cart/tomboftutankhame02cart_djvu.txt
get carter_vol3.txt      https://archive.org/download/in.gov.ignca.17096/17096_djvu.txt
get kjv_bible.txt        https://www.gutenberg.org/cache/epub/10/pg10.txt
get declaration.txt      https://www.gutenberg.org/cache/epub/1/pg1.txt
get bill_of_rights.txt   https://www.gutenberg.org/cache/epub/2/pg2.txt
get constitution.txt     https://www.gutenberg.org/cache/epub/5/pg5.txt
get poe_works_vol1.txt   https://www.gutenberg.org/cache/epub/2147/pg2147.txt
get tutankhamen_1923.txt https://www.gutenberg.org/cache/epub/59783/pg59783.txt
