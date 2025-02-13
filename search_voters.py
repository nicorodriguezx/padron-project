import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def load_voters(file_path):
    """Load voters data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_dataframe(voters):
    """Convert voters list to DataFrame and add computed columns"""
    df = pd.DataFrame(voters)
    
    # Extract location names for easier filtering
    df['localidad_nombre'] = df['localidad'].apply(lambda x: x['nombre'])
    df['departamento_nombre'] = df['departamento'].apply(lambda x: x['nombre'])
    
    # Address is already a string, no need to extract street/number
    
    return df

def search_voters(df, localidad=None, street=None, number_from=None, number_to=None):
    """Search voters based on location criteria"""
    mask = pd.Series(True, index=df.index)
    
    if localidad:
        # Search in both code and name
        mask &= (df['localidad_codigo'].str.contains(str(localidad), case=False, na=False) |
                df['localidad_nombre'].str.contains(localidad, case=False, na=False))
    
    if street:
        mask &= df['street'].str.contains(street, case=False, na=False)
    
    if number_from is not None and number_to is not None:
        # Only include rows where number is numeric and within range
        numeric_mask = pd.to_numeric(df['number'], errors='coerce').notna()
        number_mask = (pd.to_numeric(df['number'], errors='coerce') >= number_from) & \
                     (pd.to_numeric(df['number'], errors='coerce') <= number_to)
        mask &= numeric_mask & number_mask
    
    return df[mask]

def format_results(df):
    """Format results for display"""
    # Select and reorder columns
    columns = [
        'name', 'dni', 'birth_year', 'gender', 
        'localidad_nombre', 'street', 'number', 'doc_type'
    ]
    
    # Rename columns for display
    column_names = {
        'name': 'Nombre',
        'dni': 'DNI',
        'birth_year': 'Año Nac.',
        'gender': 'Género',
        'localidad_nombre': 'Localidad',
        'street': 'Calle',
        'number': 'Número',
        'doc_type': 'Documento'
    }
    
    return df[columns].rename(columns=column_names)

def plot_street_layout(results_df, street_name, output_dir):
    """Create a visualization of voters on the street"""
    # Create an explicit copy of the DataFrame
    df = results_df.copy()
    
    # Calculate current age
    current_year = datetime.now().year
    df['age'] = current_year - df['birth_year']
    
    # Separate odd and even numbers
    odd_mask = pd.to_numeric(df['number'], errors='coerce') % 2 == 1
    even_mask = pd.to_numeric(df['number'], errors='coerce') % 2 == 0
    
    odd_houses = df[odd_mask].sort_values('number')
    even_houses = df[even_mask].sort_values('number')
    
    # Calculate dimensions based on data
    max_voters_at_address = max(df.groupby('number').size())
    total_addresses = len(df['number'].unique())
    
    # Adjust figure dimensions
    # Base width is 15, but increase if many addresses
    width = max(15, total_addresses * 1.5)
    # Base height is 8, but increase if many voters at same address
    height = max(8, max_voters_at_address * 1.2)
    
    # Create the plot with calculated dimensions
    plt.figure(figsize=(width, height))
    
    # Plot settings
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)  # Street line
    plt.title(f'Distribución de votantes en calle {street_name}')
    
    # Calculate vertical spacing based on number of voters
    vertical_spacing = min(0.7, 5 / max_voters_at_address) if max_voters_at_address > 0 else 0.7
    
    # Function to plot voters at an address
    def plot_voters_at_address(house_number, voters, is_above_street):
        base_y = 1 if is_above_street else -1
        y_direction = 1 if is_above_street else -1
        number_y = base_y + (0.5 * y_direction)
        
        # Plot house number
        plt.text(house_number, number_y, str(int(house_number)), 
                ha='center', va='center', alpha=0.7)
        
        # Plot each voter
        for i, voter in enumerate(voters):
            y_pos = base_y + (i * vertical_spacing * y_direction)
            # Adjust circle size based on figure dimensions
            circle_size = min(300, (30000 / (width * height)))
            plt.scatter(house_number, y_pos, s=circle_size, 
                       color='pink' if voter['gender'] == 'F' else 'lightblue',
                       alpha=0.6)
            plt.text(house_number, y_pos, str(int(voter['age'])), 
                    ha='center', va='center')
    
    # Group by house number and plot
    for number, group in odd_houses.groupby('number'):
        plot_voters_at_address(float(number), group.to_dict('records'), True)
    
    for number, group in even_houses.groupby('number'):
        plot_voters_at_address(float(number), group.to_dict('records'), False)
    
    # Adjust plot limits and appearance
    if len(df) > 0:
        min_num = pd.to_numeric(df['number'], errors='coerce').min()
        max_num = pd.to_numeric(df['number'], errors='coerce').max()
        
        # Add padding proportional to the range of numbers
        number_range = max_num - min_num
        padding = max(50, number_range * 0.1)
        plt.xlim(min_num - padding if min_num is not None else 0, 
                max_num + padding if max_num is not None else 100)
        
        # Calculate y limits based on maximum voters
        y_margin = max(2, (max_voters_at_address * vertical_spacing) + 1)
        plt.ylim(-y_margin, y_margin)
    else:
        plt.ylim(-2, 2)
    
    # Remove y-axis and add legend
    plt.gca().get_yaxis().set_visible(False)
    plt.scatter([], [], color='pink', alpha=0.6, s=100, label='Mujeres')
    plt.scatter([], [], color='lightblue', alpha=0.6, s=100, label='Hombres')
    plt.legend()
    
    # Add street name
    plt.text(plt.xlim()[0], 0, f'Calle {street_name}', 
            ha='right', va='center', fontsize=10)
    
    # Save plot
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / f'street_layout_{street_name}.png', 
                bbox_inches='tight', dpi=300)
    plt.close()

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_dir = script_dir / "analysis"
    
    # Load and process data
    print("Loading voter data...")
    voters = load_voters(data_dir / "all_voters.json")
    df = create_dataframe(voters)
    
    while True:
        print("\n=== Búsqueda de Votantes ===")
        print("Ingrese los criterios de búsqueda (presione Enter para omitir):")
        
        localidad = input("Localidad (código o nombre): ").strip() or None
        street = input("Calle: ").strip() or None
        
        number_from = None
        number_to = None
        if street:
            try:
                number_input = input("Rango de números (ejemplo: 100-200): ").strip()
                if number_input:
                    number_from, number_to = map(int, number_input.split('-'))
            except ValueError:
                print("Formato de números inválido. Se ignorará el rango.")
        
        # Perform search
        results = search_voters(df, localidad, street, number_from, number_to)
        
        # Display results
        if len(results) > 0:
            print(f"\nSe encontraron {len(results)} votantes:")
            formatted_results = format_results(results)
            print("\n", formatted_results.to_string(index=False))
            
            # Generate street layout visualization if street is specified
            if street:
                plot_street_layout(results, street, output_dir)
                print(f"\nVisualización guardada en: {output_dir}/street_layout_{street}.png")
            
            # Save results if requested
            save = input("\n¿Desea guardar los resultados? (s/n): ").lower().strip()
            if save == 's':
                output_file = script_dir / "search_results.csv"
                formatted_results.to_csv(output_file, index=False)
                print(f"Resultados guardados en {output_file}")
        else:
            print("\nNo se encontraron votantes con los criterios especificados.")
        
        # Ask if user wants to search again
        again = input("\n¿Desea realizar otra búsqueda? (s/n): ").lower().strip()
        if again != 's':
            break
    
    print("\n¡Gracias por usar el buscador!")

if __name__ == "__main__":
    main() 