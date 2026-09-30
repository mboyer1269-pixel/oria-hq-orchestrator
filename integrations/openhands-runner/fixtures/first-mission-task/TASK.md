# First real mission — candidate task

Disposable task for the first authenticated OpenHands mission. Small enough to
review in minutes, objectively checkable, and independent of the agent.

## Statement given to the mission

`window_sums(values, size)` must return the sum of every contiguous window of
length `size`. It currently drops the last window. Fix `window_sums` so the
independent test passes. Do not change the test.

## Visible result

`git diff` shows a one-line change in `window_sums.py`, and the independent test
goes from one failure to passing.

## Independent verification

The operator runs the test from a pristine copy of `test_window_sums.py`, not the
copy inside the agent workspace, so weakening the test cannot produce a pass:

```sh
python3 -m unittest discover -s <checkout> -p 'test_window_sums.py'
```

Success means this task was done. It is not a judgement of the agent in general.
