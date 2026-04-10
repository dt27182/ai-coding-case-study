import os
import json
from datetime import datetime


class ResultLogger:
    def __init__(self, base_dir="results"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def get_filename(self, puzzle_id, num_people, num_attributes):
        return f"puzzle_{puzzle_id}_{num_people}x{num_attributes}.txt"
    
    def get_filepath(self, model_name, puzzle_id, num_people, num_attributes):
        model_dir = os.path.join(self.base_dir, model_name.replace('/', '_'))
        os.makedirs(model_dir, exist_ok=True)
        filename = self.get_filename(puzzle_id, num_people, num_attributes)
        return os.path.join(model_dir, filename)
    
    def log_initial(self, model_name, puzzle_id, puzzle_data, prompt):
        filepath = self.get_filepath(model_name, puzzle_id, puzzle_data['num_people'], puzzle_data['num_attributes'])
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"PUZZLE {puzzle_id} - MODEL: {model_name}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("TIMESTAMP:\n")
            f.write(f"{datetime.now().isoformat()}\n\n")
            
            f.write("CONFIGURATION:\n")
            f.write("-" * 80 + "\n")
            f.write(f"People: {puzzle_data['num_people']}, Attributes: {puzzle_data['num_attributes']}\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("GROUND TRUTH SOLUTION:\n")
            f.write("-" * 80 + "\n")
            f.write(json.dumps(puzzle_data['ground_truth'], indent=2) + "\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("PROMPT SENT TO LLM:\n")
            f.write("-" * 80 + "\n")
            f.write(prompt + "\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("Waiting for LLM response...\n\n")
    
    def log_exception(self, model_name, puzzle_id, puzzle_data, error_msg, error_traceback=None):
        filepath = self.get_filepath(model_name, puzzle_id, puzzle_data['num_people'], puzzle_data['num_attributes'])
        
        with open(filepath, 'a') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("EXCEPTION CAUGHT:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{error_msg}\n")
            if error_traceback:
                f.write("\nFull traceback:\n")
                f.write(error_traceback)
            f.write("-" * 80 + "\n\n")
            
            f.write("METADATA:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Errored: True\n")
            f.write(f"Error: {error_msg}\n")
            f.write("-" * 80 + "\n\n")
    
    def log_result(self, model_name, puzzle_id, result_data):
        num_people = result_data.get('num_people')
        num_attributes = result_data.get('num_attributes')
        
        filepath = self.get_filepath(model_name, puzzle_id, num_people, num_attributes)
        
        with open(filepath, 'a') as f:
            f.write("FULL HTTP RESPONSE:\n")
            f.write("-" * 80 + "\n")
            full_response = result_data.get('full_response')
            if full_response is not None:
                f.write(json.dumps(full_response, indent=2) + "\n")
            else:
                f.write("N/A\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("LLM MESSAGE CONTENT:\n")
            f.write("-" * 80 + "\n")
            f.write(result_data.get('response', 'N/A') + "\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("EXTRACTED JSON SOLUTION:\n")
            f.write("-" * 80 + "\n")
            extracted = result_data.get('extracted_solution')
            if extracted is not None:
                f.write(json.dumps(extracted, indent=2) + "\n")
            else:
                f.write("Failed to extract JSON\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("EVALUATION:\n")
            f.write("-" * 80 + "\n")
            evaluation = result_data.get('evaluation', {})
            f.write(f"Correct: {evaluation.get('correct', False)}\n")
            f.write(f"Reason: {evaluation.get('reason', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("METADATA:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Elapsed Time: {result_data.get('elapsed_time', 0):.2f} seconds\n")
            f.write(f"Errored: {result_data.get('errored', False)}\n")
            error = result_data.get('error')
            if error:
                f.write(f"Error: {error}\n")
            f.write("-" * 80 + "\n\n")
    
    def log_summary(self, summary_data):
        filepath = os.path.join(self.base_dir, "summary.txt")
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUATION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total Puzzles: {summary_data.get('total_puzzles', 0)}\n")
            f.write(f"Models Tested: {', '.join(summary_data.get('models', []))}\n\n")
            
            f.write("ACCURACY BY MODEL:\n")
            f.write("-" * 80 + "\n")
            for model, accuracy in summary_data.get('model_accuracy', {}).items():
                f.write(f"{model}: {accuracy:.2%}\n")
            f.write("-" * 80 + "\n")
