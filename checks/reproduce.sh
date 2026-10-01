#!/bin/zsh
# Regenerate the evidence logs in results/. Quick runs by default (~10 min total);
# pass --long to also rerun the multi-hour searches (logs from the original runs are committed).
set -e
cd ${0:A:h}/..
make -s all
R=results
run() {  # run NAME CMD... : log the command, its output and the date
  local name=$1; shift
  { echo "# $*"; echo "# $(date -u +%Y-%m-%dT%H:%MZ)"; echo; eval "$@"; } > $R/$name.txt 2>&1
  echo "wrote $R/$name.txt"
}
run 01_periodic_progressive_autokey_hill  python3 attacks.py periodic progressive autokey hill
run 02_running_key_sculpture_texts        python3 attacks.py running
run 03_theme_alphabets_summary            "THEMES=1 python3 attacks.py periodic autokey running progressive | grep -v -E 'survivors: none|: none\$'"
run 04_typo_tolerance                     python3 typo.py
run 05_columnar_every_order_w2-8          bin/trans 8 8
run 06_k3_rotation                        bin/trans rot 8
python3 keywords.py > data/keyword_orders.txt
run 07_keyword_columnar_w12-30            "bin/trans ord 8 < data/keyword_orders.txt"
run 09_dictionary_alphabets_summary       "python3 dictalpha.py | awk '/^SURVIVOR/{n[\$2\" \"\$3\" period \"\$5\" checks \"\$7]++; next} {print} END{for(k in n) print \"survivors:\", k, \"->\", n[k], \"alphabets\"}'"
run 11_digit_shift                        python3 digits.py
run 12_trifid                             python3 trifid.py
run 13_quagmire_I_II_any_alphabet         python3 mixedalpha.py
run 17_layer_two                          python3 layer2.py 26
run 18_k1k3_running_key_masked            python3 runkey_mixed.py
run 19_guessed_words_periods_27-48        python3 drag.py
[[ -f data/quadgrams.bin || -f data/quadgrams_local.bin ]] || python3 checks/quadgrams_local.py
[[ -f data/quadgrams_de_local.bin ]] || python3 checks/quadgrams_local.py german
run 23_key_as_language_english            python3 keylanguage.py english
run 23b_key_as_language_german            python3 keylanguage.py german
run 24_generated_keystreams               python3 keygen.py
run 25_autokey_unknown_alphabet           python3 autokey_mixed.py
run 26_sculpture_letters_by_position      python3 gridkey.py
if [[ -d data/running_keys ]]; then
  run 10_running_key_outside_texts        python3 runkey.py
else
  echo "skip 10 (run checks/fetch_texts.sh first)"
fi
if [[ "$1" == "--long" ]]; then
  run 05b_columnar_every_order_w2-11      bin/trans 11 8
  run 08_columnar_every_order_w12-14      bin/dfs 12 14 26 8
  run 14_quagmire_III_IV_python           python3 quag34.py
  run 15_quagmire_random_calibration      python3 checks/calib_quag.py
  run 16_annealing_k4_and_random          checks/run_sa_k4.sh
fi
