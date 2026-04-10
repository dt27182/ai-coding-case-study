import argparse
import os
import re
from collections import defaultdict

def parse_logs(directory):
    # Stats structure: stats[people][attributes]['pass'/'fail'/'error'/'total']
    stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'pass': 0, 'fail': 0, 'error': 0}))
    
    file_pattern = re.compile(r'p(\d+)_a(\d+)_s(\d+)_')
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return stats
        
    for filename in os.listdir(directory):
        if not filename.endswith('.txt'):
            continue
            
        filepath = os.path.join(directory, filename)
        match = file_pattern.search(filename)
        
        if match:
            people = int(match.group(1))
            attributes = int(match.group(2))
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            header_match = re.search(r'# (\d+) people, (\d+) attributes', content)
            if header_match:
                people = int(header_match.group(1))
                attributes = int(header_match.group(2))
            else:
                continue
                
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        stats[people][attributes]['total'] += 1
        
        if ">>> ERROR" in content:
            stats[people][attributes]['error'] += 1
        elif "\nPASS\n" in content or ">>> SOLUTION COMPARISON\nPASS" in content:
            stats[people][attributes]['pass'] += 1
        elif "\nFAIL:\n" in content or "\nFAIL: " in content:
            stats[people][attributes]['fail'] += 1
        else:
            stats[people][attributes]['error'] += 1
            
    return stats

def write_grid_to_csv(f, stats, title, value_extractor):
    if not stats:
        f.write(f"No data for {title}\n\n")
        return
        
    people_keys = sorted(stats.keys())
    all_attr_keys = set()
    for p in people_keys:
        all_attr_keys.update(stats[p].keys())
    attr_keys = sorted(list(all_attr_keys))
    
    f.write(f"--- {title} ---\n")
    header = "People/Attributes," + ",".join(str(a) for a in attr_keys)
    f.write(header + "\n")
    for p in people_keys:
        row_vals = []
        for a in attr_keys:
            if a in stats[p]:
                val = value_extractor(stats[p][a])
                if isinstance(val, float):
                    row_vals.append(f"{val:.2f}")
                else:
                    row_vals.append(str(val))
            else:
                row_vals.append("")
        f.write(f"{p}," + ",".join(row_vals) + "\n")
    f.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze logic puzzle run logs")
    parser.add_argument("log_dir", help="Directory containing log files")
    args = parser.parse_args()
    
    stats = parse_logs(args.log_dir)
    
    if not stats:
        print("No stats were parsed from the directory.")
        return
        
    output_file = "analysis_results.csv"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 1. Correct runs
        write_grid_to_csv(f, stats, "Correct Runs (PASS)", lambda s: s['pass'])
        
        # 2. Total runs
        write_grid_to_csv(f, stats, "Total Runs", lambda s: s['total'])
        
        # 3. Pass rates (CSV format)
        write_grid_to_csv(f, stats, "Pass Rates", lambda s: s['pass'] / s['total'] if s['total'] > 0 else 0.0)
        
        # 4. Error runs
        write_grid_to_csv(f, stats, "Errored Runs (ERROR)", lambda s: s['error'])
        
    print(f"Wrote all analysis results to {output_file}")

if __name__ == "__main__":
    main()
