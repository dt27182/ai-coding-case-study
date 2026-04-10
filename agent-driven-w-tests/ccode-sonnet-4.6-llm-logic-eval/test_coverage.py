import time
from generate_puzzle import generate_puzzle

bounds = [(3,3,12,14),(5,5,35,50),(8,8,89,150),(10,10,140,250),(15,15,517,650),(20,20,1240,1300)]

for n, m, lo, hi in bounds:
    t0 = time.time()
    counts = [generate_puzzle(n, m)['num_clues'] for _ in range(3)]
    elapsed = time.time() - t0
    ok = all(lo <= c <= hi for c in counts)
    print(f"{n}x{m}: {counts} expected[{lo},{hi}] {'OK' if ok else 'FAIL'} in {elapsed:.2f}s")
