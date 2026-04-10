import argparse
import csv
import os
import re
from collections import defaultdict


def parse_result(content):
    if '>>> DRY RUN' in content:
        return None
    if '>>> ERROR' in content:
        return 'error'
    m = re.search(r'>>> SOLUTION COMPARISON\n\n(\w+)', content)
    if m:
        return 'pass' if m.group(1) == 'PASS' else 'fail'
    return None


def parse_filename(name):
    m = re.match(r'p(\d+)_a(\d+)_s\d+_\d+_\d+\.txt$', name)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def build_grid(label, rows, cols, cell_fn):
    grid = [[label] + [f'a{c}' for c in cols]]
    for r in rows:
        grid.append([f'p{r}'] + [cell_fn(r, c) for c in cols])
    return grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('log_dir')
    parser.add_argument('-o', '--output', default='analysis.csv')
    args = parser.parse_args()

    correct = defaultdict(int)
    total = defaultdict(int)
    errors = defaultdict(int)

    for fname in os.listdir(args.log_dir):
        num_people, num_attrs = parse_filename(fname)
        if num_people is None:
            continue
        with open(os.path.join(args.log_dir, fname)) as f:
            content = f.read()
        result = parse_result(content)
        if result is None:
            continue
        key = (num_people, num_attrs)
        total[key] += 1
        if result == 'pass':
            correct[key] += 1
        elif result == 'error':
            errors[key] += 1

    if not total:
        print("No log files found.")
        return

    rows = sorted({k[0] for k in total})
    cols = sorted({k[1] for k in total})

    grids = [
        build_grid('Correct Counts', rows, cols,
                   lambda r, c: str(correct.get((r, c), 0))),
        build_grid('Total Counts', rows, cols,
                   lambda r, c: str(total.get((r, c), 0))),
        build_grid('Pass Rates', rows, cols,
                   lambda r, c: f"{correct.get((r, c), 0) / total[(r, c)]:.2f}" if total.get((r, c)) else '-'),
        build_grid('Error Counts', rows, cols,
                   lambda r, c: str(errors.get((r, c), 0))),
    ]

    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        for i, grid in enumerate(grids):
            if i > 0:
                writer.writerow([])
            for row in grid:
                writer.writerow(row)

    print(f"Analysis written to {args.output}")


if __name__ == '__main__':
    main()
