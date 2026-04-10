
import random
import time
from src.generator import LogicPuzzle

def run_experiment(max_n=5, max_m=5):
    print("N, M, MinClues, AvgClues, MaxClues, AvgTotalCands, Ratio(Min/Total)")
    
    for n in range(2, max_n + 1):
        for m in range(2, max_m + 1):
            
            # Run a few trials to average
            trials = 5
            results = []
            total_cand_counts = []
            
            for t in range(trials):
                puzzle = LogicPuzzle(n, m)
                puzzle.generate_ground_truth()
                
                # Generate ALL possible clues first using the shared method
                all_candidates = puzzle._generate_candidate_clues()
                random.shuffle(all_candidates)
                total_cand_counts.append(len(all_candidates))
                
                # Now incrementally add and check
                active_constraints = []
                needed = 0
                
                # Step size optimization
                step = 1
                
                found = False
                for i in range(0, len(all_candidates), step):
                    # Add batch
                    batch = all_candidates[needed : i+step]
                    if not batch: break
                    active_constraints.extend(batch)
                    needed = len(active_constraints)
                    
                    sol_count = puzzle.solve(active_constraints, max_solutions=2)
                    if sol_count == 1:
                       found = True
                       break
                
                if found:
                    results.append(needed)
                else:
                    results.append(len(all_candidates)) # Failed to converge
            
            if results:
                min_needed = min(results)
                max_needed = max(results)
                avg_needed = sum(results) / len(results)
                avg_total = sum(total_cand_counts) / len(total_cand_counts)
                ratio = min_needed / avg_total if avg_total > 0 else 0
                print(f"{n}, {m}, {min_needed}, {avg_needed:.1f}, {max_needed}, {avg_total:.1f}, {ratio:.2f}")

if __name__ == "__main__":
    run_experiment()
