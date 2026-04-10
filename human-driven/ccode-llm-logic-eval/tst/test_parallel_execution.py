import sys
import os
import time
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
import execute_tests

SLEEP_DURATION = 0.3
NUM_INVOCATIONS = 4  # p2-3 x a2-3, 1 model, 1 sample each

start_times = []
lock = threading.Lock()


def mock_generate_puzzle(num_people, num_attrs):
    with lock:
        start_times.append(time.time())
    time.sleep(SLEEP_DURATION)
    solution = [{"Position": i, "Name": f"Person{i}"} for i in range(num_people)]
    return {"solution": solution, "clues": []}


with patch('sys.argv', ['execute_tests', '-p', '2', '-P', '3', '-a', '2', '-A', '3',
                        '-n', '1', '-m', 'test-model', '--dry-run']):
    with patch.dict(os.environ, {'OPEN_ROUTER_TOKEN': 'fake_token'}):
        with patch('execute_tests.generate_puzzle', side_effect=mock_generate_puzzle):
            with patch('execute_tests.OpenAI', return_value=MagicMock()):
                wall_start = time.time()
                execute_tests.main()
                wall_elapsed = time.time() - wall_start

assert len(start_times) == NUM_INVOCATIONS, \
    f"FAIL: expected {NUM_INVOCATIONS} invocations, got {len(start_times)}"

sequential_time = NUM_INVOCATIONS * SLEEP_DURATION
assert wall_elapsed < sequential_time, \
    f"FAIL: wall time {wall_elapsed:.2f}s >= sequential time {sequential_time:.2f}s — not running in parallel"

print(f"PASS: {NUM_INVOCATIONS} invocations completed in {wall_elapsed:.2f}s "
      f"(sequential would be {sequential_time:.2f}s)")
