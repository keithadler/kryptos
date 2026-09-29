#!/bin/zsh
# K4 and 3 random ciphertexts through one-free-alphabet Quagmire annealing at the untestable periods.
cd ${0:A:h}
for m in 1 2 5 6; do
  for p in 13 16 19 20 23 24 26; do
    k4=$(CRIBW=10 ./sa $m $p 16 4000000 "" $p | grep '^restart' | sort -k4 -g -r | head -1)
    echo "K4     mode $m period $p  $k4"
  done
done
for s in 1 2 3; do
  r=$(python3 -c "import random; r=random.Random($s); print(''.join(r.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(97)))")
  for m in 1 2; do
    for p in 13 20; do
      out=$(CRIBW=10 ./sa $m $p 16 4000000 "$r" $p | grep '^restart' | sort -k4 -g -r | head -1)
      echo "RANDOM$s mode $m period $p  $out"
    done
  done
done
