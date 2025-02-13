import pdfplumber
import json
import re
from pathlib import Path

def extract_location_info(text):
    """Extract departamento and localidad from header"""
    dept_match = re.search(r'(\d+)-([^0-9\n]+)', text)
    loc_match = re.search(r'(\d{4})-([^0-9\n]+)', text)
    
    return {
        "departamento": {
            "codigo": dept_match.group(1) if dept_match else None,
            "nombre": dept_match.group(2).strip() if dept_match else None
        },
        "localidad": {
            "codigo": loc_match.group(1) if loc_match else None,
            "nombre": loc_match.group(2).strip() if loc_match else None
        }
    }

def parse_address(address):
    """Clean up address string"""
    return address.strip()

def parse_voter_line(line, location_info):
    """Parse a single line from the voter registry"""
    # Pattern: number DNI year NAME,ADDRESS, DOC-TYPE GENDER
    pattern = r'^\d+\s+(\d{8})\s+(\d{4})\s+([^,]+),([^,]+),\s*([^\s]+)\s+([MF])'
    match = re.match(pattern, line.strip())
    if match:
        return {
            "departamento": location_info["departamento"],
            "localidad": location_info["localidad"],
            "dni": match.group(1),
            "birth_year": int(match.group(2)),
            "name": match.group(3).strip(),
            "address": parse_address(match.group(4)),
            "doc_type": match.group(5).strip(),
            "gender": match.group(6)
        }
    return None

def get_all_voters(pdf_path):
    """Extract all voters and location info from the PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            
            # Extract location information
            location_info = extract_location_info(text)
            
            # Split into lines
            lines = text.split('\n')
            
            # Find where the actual data starts (after headers)
            start_idx = 0
            for i, line in enumerate(lines):
                if 'CLASEAPELLIDO' in line or 'DOCUMENTO GEN' in line:
                    start_idx = i + 1
                    break
            
            # Process all voter lines
            voters = []
            for line in lines[start_idx:]:
                if re.match(r'^\d+\s+\d{8}', line):
                    voter_data = parse_voter_line(line, location_info)
                    if voter_data:
                        voters.append(voter_data)
            
            return voters

    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return None

def save_to_json(data, output_path):
    """Save data to JSON file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_all_pages(split_pages_dir, output_dir):
    """Process all page_x.pdf files in the directory"""
    # Get all PDF files sorted numerically
    pdf_files = sorted(
        split_pages_dir.glob("page_*.pdf"),
        key=lambda x: int(x.stem.split('_')[1])
    )
    
    total_voters = []
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        voters = get_all_voters(pdf_file)
        if voters:
            total_voters.extend(voters)
            # Save individual page results
            page_output = output_dir / f"{pdf_file.stem}.json"
            save_to_json(voters, page_output)
            print(f"Extracted {len(voters)} voters from {pdf_file.name}")
        else:
            print(f"Failed to extract data from {pdf_file.name}")
    
    # Save combined results
    if total_voters:
        combined_output = output_dir / "all_voters.json"
        save_to_json(total_voters, combined_output)
        print(f"\nTotal voters extracted: {len(total_voters)}")
        print(f"Combined data saved to {combined_output}")
    
    return len(total_voters)

def main():
    script_dir = Path(__file__).parent
    split_pages_dir = script_dir / "split_pages"
    output_dir = script_dir / "data"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all pages
    total_voters = process_all_pages(split_pages_dir, output_dir)
    
    if total_voters > 0:
        print("\nProcessing completed successfully!")
    else:
        print("\nNo data was extracted")

if __name__ == "__main__":
    main()