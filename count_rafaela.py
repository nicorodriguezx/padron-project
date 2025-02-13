import json

def count_rafaela_voters():
    # Read the JSON file
    with open('data/all_voters.json', 'r', encoding='utf-8') as file:
        voters = json.load(file)
    
    # Count voters from Rafaela (case insensitive)
    rafaela_count = sum(
        1 for voter in voters 
        if isinstance(voter.get('localidad', ''), str) and voter.get('localidad', '').lower() == 'rafaela'
    )
    
    print(f"Total voters from Rafaela: {rafaela_count}")

if __name__ == '__main__':
    count_rafaela_voters() 