# Combinatorics Toolkit

An upgrade of the original "factorial of a number" notebook into a full
combinatorics library: factorials (four algorithms), permutations,
combinations, Stirling numbers of the second kind, Bell numbers,
derangements, multinomial coefficients, trailing zeros, and the Gamma
extension of factorial to non-integers.

## Features

- `combinatorics.py` — the library:
  - `factorial(n, method=...)` with `iterative`, `memoized`, `prime`
    (Legendre prime-factorization), `stdlib`, `auto`
  - `permutations(n, r)`, `combinations(n, r)` (overflow-safe
    multiplicative formula)
  - `stirling2(n, k)`, `bell_number(n)`, `derangements(n)`,
    `multinomial(n, groups)`, `trailing_zeros(n)`
  - `gamma_factorial(x)` — factorial for non-integers via Gamma(x+1)
- `benchmark.py` — shootout of the four factorial algorithms with
  `timeit` (best of 5)
- `growth_chart.py` — matplotlib log-scale chart of n!, central
  binomial coefficients, and Bell numbers (`growth_rates.png`)
- `examples.py` — real probability problems: poker hands, 6/49
  lottery odds, committee selection, the hat-check problem,
  password-space counting

## How to run

```bash
pip install -r requirements.txt   # only matplotlib, for the chart
python examples.py                # probability examples
python benchmark.py               # algorithm timings
python growth_chart.py            # writes growth_rates.png
```

```python
from combinatorics import combinations, stirling2
combinations(52, 5)   # 2598960 possible poker hands
stirling2(10, 3)      # 9330 ways to split 10 items into 3 groups
```

## Examples

```
P(exactly 2 aces in poker hand) = 0.039930
P(6/49 lottery jackpot)         = 1 in 13,983,816
3-person committees from 10     = 120
P(nobody gets own hat, n=10)    = 0.367879 (1/e = 0.367879)
8-char alphanumeric passwords   = 218,340,105,584,896
```
