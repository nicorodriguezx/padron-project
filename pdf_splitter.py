from PyPDF2 import PdfReader, PdfWriter
import os
import argparse

def split_pdf(input_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Create PDF reader object
    reader = PdfReader(input_path)
    
    # Get total number of pages
    total_pages = len(reader.pages)
    
    # Extract each page
    for page_num in range(total_pages):
        # Create PDF writer object
        writer = PdfWriter()
        
        # Add the current page
        writer.add_page(reader.pages[page_num])
        
        # Generate output filename
        output_filename = os.path.join(
            output_folder,
            f'page_{page_num + 1}.pdf'
        )
        
        # Write the page to a file
        with open(output_filename, 'wb') as output_file:
            writer.write(output_file)
            
        print(f'Created: {output_filename}')
    
    print(f'Successfully split {total_pages} pages')

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Split a PDF file into individual pages')
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('--output-dir', '-o', 
                        default='split_pages',
                        help='Output directory for split pages (default: split_pages)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the split operation
    split_pdf(args.input_pdf, args.output_dir) 