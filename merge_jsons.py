import json
from pathlib import Path

def merge_json_files(data_dir):
    """Merge all JSON files in the data directory"""
    # Get all JSON files except all_voters.json
    json_files = [f for f in sorted(
        data_dir.glob("page_*.json"),
        key=lambda x: int(x.stem.split('_')[1])
    )]
    
    print(f"Found {len(json_files)} JSON files to merge")
    
    all_voters = []
    
    # Process each file
    for json_file in json_files:
        print(f"Processing {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                voters = json.load(f)
                if isinstance(voters, list):
                    all_voters.extend(voters)
                    print(f"Added {len(voters)} voters from {json_file.name}")
                else:
                    print(f"Warning: {json_file.name} does not contain a list of voters")
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
    
    return all_voters

def save_merged_json(voters, output_path):
    """Save merged data to JSON file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(voters, f, ensure_ascii=False, indent=2)
        print(f"\nSuccessfully saved {len(voters)} voters to {output_path}")
    except Exception as e:
        print(f"Error saving merged file: {e}")

def main():
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_file = data_dir / "all_voters.json"
    
    print("Starting JSON merge process...")
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        return
    
    # Merge all JSON files
    all_voters = merge_json_files(data_dir)
    
    if all_voters:
        # Sort voters by DNI before saving
        all_voters.sort(key=lambda x: x['dni'])
        
        # Save merged data
        save_merged_json(all_voters, output_file)
        print("\nMerge completed successfully!")
        print(f"Total voters in merged file: {len(all_voters)}")
    else:
        print("\nNo data was merged")

if __name__ == "__main__":
    main() 