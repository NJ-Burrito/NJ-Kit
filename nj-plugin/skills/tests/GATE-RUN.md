# v3 gate run — 2026-09-22T11:24:43+03:00 (estimator round)

$ tests/test_v3.py -> rc=0
TESTS: 79 passed, 0 failed
$ nj-delegate/scripts/check_governance.py --selftest -> rc=0
ok   --run: overlapping OWNED_PATHS (prefix) is caught
$ nj-delegate/scripts/check_governance.py --tally -> rc=0
tally: 8 gates, 8 habits, 0 naming a missing script
$ nj-delegate/scripts/check_governance.py --project <project-root> -> rc=0
governance check: 5/5 pass, 0 fail
$ nj-delegate/scripts/check_governance.py --run .agent-ops/briefs/v3-build -> rc=0
run check: 4 briefs, 0 overlap(s)

## forecaster
$ estimate thin class -> rc=1 (refuses)
$ estimate healthy class -> rc=0

## live calibration (this workspace)
estimate calibration: n scored=1 MAPE=60.00% p80 hit=100.00% bias=over-estimating (median signed error -3.0 min)
estimate calibration: MAPE 60.00% (target <=30), p80 hit 100.00% (target >=80) basis=n=1 BREACH
