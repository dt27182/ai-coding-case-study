import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from generate_puzzle import generate_puzzle

TIMEOUT = 10
SIZES = [
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (8, 8),
    (10, 10),
    (12, 12),
    (15, 15),
    (20, 20),
]

for num_people, num_attributes in SIZES:
    with ThreadPoolExecutor(max_workers=1) as executor:
        start = time.time()
        future = executor.submit(generate_puzzle, num_people, num_attributes)
        try:
            puzzle = future.result(timeout=TIMEOUT)
            elapsed = time.time() - start
            print(f"{num_people}x{num_attributes}: {len(puzzle['clues'])} clues in {elapsed:.2f}s")
        except FuturesTimeoutError:
            print(f"{num_people}x{num_attributes}: TIMEOUT (>{TIMEOUT}s)")
