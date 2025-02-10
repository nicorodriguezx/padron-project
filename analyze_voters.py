import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns

def load_voters(file_path):
    """Load voters data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_age(birth_year):
    """Calculate age from birth year"""
    current_year = datetime.now().year
    return current_year - birth_year

def create_age_groups(age):
    """Create age groups for better visualization"""
    if age < 26:
        return '16-25'
    elif age < 36:
        return '26-35'
    elif age < 46:
        return '36-45'
    elif age < 56:
        return '46-55'
    elif age < 66:
        return '56-65'
    elif age < 76:
        return '66-75'
    else:
        return '76+'

def analyze_demographics(voters):
    """Convert voters data to pandas DataFrame and add calculated fields"""
    df = pd.DataFrame(voters)
    
    # Add age and age group columns
    df['age'] = df['birth_year'].apply(calculate_age)
    df['age_group'] = df['age'].apply(create_age_groups)
    
    # Extract localidad info
    df['localidad'] = df['localidad'].apply(lambda x: f"{x['codigo']}-{x['nombre']}")
    
    return df

def generate_gender_stats(df):
    """Generate gender statistics per localidad"""
    # Calculate gender counts and percentages
    gender_stats = df.groupby('localidad')['gender'].value_counts().unstack(fill_value=0)
    gender_stats['total'] = gender_stats['F'] + gender_stats['M']
    gender_stats['F_pct'] = (gender_stats['F'] / gender_stats['total'] * 100).round(1)
    gender_stats['M_pct'] = (gender_stats['M'] / gender_stats['total'] * 100).round(1)
    
    return gender_stats

def generate_age_stats(df):
    """Generate age statistics per localidad"""
    # Calculate age group counts
    age_stats = df.groupby(['localidad', 'age_group']).size().unstack(fill_value=0)
    
    # Add percentage columns
    totals = age_stats.sum(axis=1)
    age_pcts = age_stats.div(totals, axis=0) * 100
    age_pcts = age_pcts.round(1)
    
    return age_stats, age_pcts

def plot_gender_distribution(gender_stats, output_dir):
    """Create gender distribution plot"""
    plt.figure(figsize=(12, 6))
    
    x = range(len(gender_stats.index))
    width = 0.35
    
    plt.bar(x, gender_stats['F_pct'], width, label='Mujeres', color='pink')
    plt.bar([i + width for i in x], gender_stats['M_pct'], width, label='Hombres', color='lightblue')
    
    plt.xlabel('Localidad')
    plt.ylabel('Porcentaje')
    plt.title('Distribución de Género por Localidad')
    plt.xticks([i + width/2 for i in x], gender_stats.index, rotation=45, ha='right')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'gender_distribution.png')
    plt.close()

def plot_age_distribution(age_stats, age_pcts, output_dir):
    """Create age distribution plots"""
    # Absolute numbers
    plt.figure(figsize=(12, 6))
    age_stats.plot(kind='bar', stacked=True)
    plt.title('Distribución de Edades por Localidad (Números Absolutos)')
    plt.xlabel('Localidad')
    plt.ylabel('Cantidad de Votantes')
    plt.legend(title='Grupo Etario', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(output_dir / 'age_distribution_absolute.png')
    plt.close()
    
    # Percentages
    plt.figure(figsize=(12, 6))
    age_pcts.plot(kind='bar', stacked=True)
    plt.title('Distribución de Edades por Localidad (Porcentajes)')
    plt.xlabel('Localidad')
    plt.ylabel('Porcentaje')
    plt.legend(title='Grupo Etario', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(output_dir / 'age_distribution_percentage.png')
    plt.close()

def save_stats_to_csv(gender_stats, age_stats, age_pcts, output_dir):
    """Save statistical data to CSV files"""
    gender_stats.to_csv(output_dir / 'gender_stats.csv')
    age_stats.to_csv(output_dir / 'age_stats.csv')
    age_pcts.to_csv(output_dir / 'age_percentages.csv')

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_dir = script_dir / "analysis"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and process data
    print("Loading voter data...")
    voters = load_voters(data_dir / "all_voters.json")
    
    print("Analyzing demographics...")
    df = analyze_demographics(voters)
    
    # Generate statistics
    print("Generating statistics...")
    gender_stats = generate_gender_stats(df)
    age_stats, age_pcts = generate_age_stats(df)
    
    # Create visualizations
    print("Creating visualizations...")
    plot_gender_distribution(gender_stats, output_dir)
    plot_age_distribution(age_stats, age_pcts, output_dir)
    
    # Save statistics to CSV
    print("Saving statistics to CSV...")
    save_stats_to_csv(gender_stats, age_stats, age_pcts, output_dir)
    
    print("\nAnalysis completed! Results saved to the 'analysis' directory:")
    print("- Gender distribution plot: gender_distribution.png")
    print("- Age distribution plots: age_distribution_absolute.png and age_distribution_percentage.png")
    print("- Statistics in CSV format: gender_stats.csv, age_stats.csv, and age_percentages.csv")

if __name__ == "__main__":
    main() 