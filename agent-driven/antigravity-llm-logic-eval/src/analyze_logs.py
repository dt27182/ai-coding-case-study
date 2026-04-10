
import os
import re
import csv
import argparse
from collections import defaultdict
from typing import Dict, Tuple

def analyze_logs(log_dir: str, output_file: str):
    # Data structures: (n, m) -> count
    correct_counts = defaultdict(int)
    total_counts = defaultdict(int)
    error_counts = defaultdict(int)
    
    # Track all N and M values encountered
    n_values = set()
    m_values = set()

    for root, _, files in os.walk(log_dir):
        for file in files:
            if not file.endswith(".txt"):
                continue
            
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Extract Size
            size_match = re.search(r"Size: (\d+) people, (\d+) attributes", content)
            if not size_match:
                # Might be detailed error log without size? Skip for now or try to infer from filename?
                # Filename format: puzzle_ID_N_M.txt
                # puzzle_1_9_9.txt
                filename_match = re.match(r"puzzle_\d+_(\d+)_(\d+)\.txt", file)
                if filename_match:
                    n = int(filename_match.group(1))
                    m = int(filename_match.group(2))
                else:
                    continue
            else:
                n = int(size_match.group(1))
                m = int(size_match.group(2))
            
            n_values.add(n)
            m_values.add(m)
            total_counts[(n, m)] += 1
            
            # Extract Correctness
            correct_match = re.search(r"Correct: (True|False)", content)
            is_correct = False
            if correct_match:
                is_correct = correct_match.group(1) == "True"
                if is_correct:
                    correct_counts[(n, m)] += 1
            
            # Extract Error Status
            # Check for explicitly logged errors or Status not Success
            # Generation/Evaluation errors
            is_error = False
            if "STATUS: GENERATION_ERROR" in content or "STATUS: EVALUATION_ERROR" in content:
                is_error = True
            
            status_match = re.search(r"Status: (.+)", content)
            if status_match:
                status = status_match.group(1).strip()
                if status != "Correct" or not status.startswith("Mismatch at Position"):
                    is_error = True
            
            if is_error:
                error_counts[(n, m)] += 1

    # Sort dimensions
    sorted_n = sorted(list(n_values))
    sorted_m = sorted(list(m_values))
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Helper to write a matrix
        def write_matrix(title, data_dict, as_percentage=False):
            writer.writerow([title])
            # Headers: M values
            headers = ["N \\ M"] + [str(m) for m in sorted_m]
            writer.writerow(headers)
            
            for n in sorted_n:
                row = [str(n)]
                for m in sorted_m:
                    val = data_dict[(n, m)]
                    if as_percentage:
                        total = total_counts[(n, m)]
                        if total > 0:
                            pct = (val / total) 
                            row.append(f"{pct:.2f}")
                        else:
                            row.append("N/A")
                    else:
                        row.append(str(val))
                writer.writerow(row)
            writer.writerow([]) # Empty line
            
        write_matrix("Correct Counts", correct_counts)
        write_matrix("Total Counts", total_counts)
        # Pass Rate: uses correct_counts but with percentage logic
        write_matrix("Pass Rates", correct_counts, as_percentage=True)
        write_matrix("Error Counts", error_counts)

    print(f"Analysis complete. Written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze puzzle logs.")
    parser.add_argument("log_dir", help="Directory containing log files")
    parser.add_argument("--output", default="analysis.csv", help="Output CSV file path")
    args = parser.parse_args()
    
    analyze_logs(args.log_dir, args.output)
