from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import pandas as pd
from datetime import datetime
from search_voters import load_voters, create_dataframe
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

app = Flask(__name__)

# Load data at startup
script_dir = Path(__file__).parent
data_dir = script_dir / "data"
voters = load_voters(data_dir / "all_voters.json")
df = create_dataframe(voters)

# Calculate current year for age calculations
CURRENT_YEAR = datetime.now().year

@app.route('/')
def index():
    # Get unique localities sorted alphabetically
    localities = sorted(df['localidad_nombre'].unique())
    return render_template('index.html', localities=localities)

@app.route('/search')
def search():
    # Get search parameters
    localidad = request.args.get('localidad')
    gender = request.args.get('gender')
    name = request.args.get('name')
    age_from = request.args.get('age_from', type=int)
    age_to = request.args.get('age_to', type=int)
    page = request.args.get('page', 1, type=int)
    
    # If no parameters are provided, return empty results
    if not any([localidad, gender != 'all', name, age_from, age_to]):
        return jsonify({
            'results': [],
            'total_results': 0,
            'total_pages': 0,
            'current_page': 1
        })
    
    # Start with all records
    mask = pd.Series(True, index=df.index)
    
    # Apply filters
    if localidad and localidad != 'all':
        mask &= df['localidad_nombre'] == localidad
    
    if gender and gender != 'all':
        mask &= df['gender'] == gender
    
    if name:
        mask &= df['name'].str.contains(name, case=False, na=False)
    
    if age_from is not None and age_to is not None:
        birth_year_to = CURRENT_YEAR - age_from
        birth_year_from = CURRENT_YEAR - age_to
        mask &= (df['birth_year'] >= birth_year_from) & (df['birth_year'] <= birth_year_to)
    
    # Get filtered results
    results = df[mask].copy()  # Create a copy to avoid SettingWithCopyWarning
    
    # Calculate pagination
    per_page = 20
    total_results = len(results)
    total_pages = max(1, (total_results + per_page - 1) // per_page)
    
    # Get paginated results
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results.iloc[start_idx:end_idx]
    
    # Format results for display
    formatted_results = []
    for _, row in paginated_results.iterrows():
        age = CURRENT_YEAR - row['birth_year']
        formatted_results.append({
            'name': str(row['name']),  # Ensure string type
            'dni': str(row['dni']),    # Ensure string type
            'age': int(age),
            'gender': 'Femenino' if row['gender'] == 'F' else 'Masculino',
            'localidad': str(row['localidad_nombre']),
            'address': str(row['address'])
        })
    
    response = {
        'results': formatted_results,
        'total_results': total_results,
        'total_pages': total_pages,
        'current_page': page
    }
    
    return jsonify(response)

def get_filtered_results():
    """Get filtered results based on search parameters"""
    localidad = request.args.get('localidad')
    gender = request.args.get('gender')
    name = request.args.get('name')
    age_from = request.args.get('age_from', type=int)
    age_to = request.args.get('age_to', type=int)
    
    # Start with all records
    mask = pd.Series(True, index=df.index)
    
    # Apply filters
    if localidad and localidad != 'all':
        mask &= df['localidad_nombre'] == localidad
    
    if gender and gender != 'all':
        mask &= df['gender'] == gender
    
    if name:
        mask &= df['name'].str.contains(name, case=False, na=False)
    
    if age_from is not None and age_to is not None:
        birth_year_to = CURRENT_YEAR - age_from
        birth_year_from = CURRENT_YEAR - age_to
        mask &= (df['birth_year'] >= birth_year_from) & (df['birth_year'] <= birth_year_to)
    
    return df[mask].copy()

@app.route('/export/xlsx')
def export_xlsx():
    results = get_filtered_results()
    
    # Format results for export
    export_df = pd.DataFrame({
        'Nombre': results['name'],
        'DNI': results['dni'],
        'Edad': CURRENT_YEAR - results['birth_year'],
        'Género': results['gender'].map({'F': 'F', 'M': 'M'}),
        'Dirección': results['address'],
        'Localidad': results['localidad_nombre']
    })
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Resultados')
        # Auto-adjust columns' width
        worksheet = writer.sheets['Resultados']
        for idx, col in enumerate(export_df.columns):
            series = export_df[col]
            max_len = max(
                series.astype(str).map(len).max(),
                len(str(col))
            ) + 1
            worksheet.set_column(idx, idx, max_len)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'votantes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@app.route('/export/pdf')
def export_pdf():
    results = get_filtered_results()
    
    # Format results for export
    export_df = pd.DataFrame({
        'Nombre': results['name'],
        'DNI': results['dni'],
        'Edad': CURRENT_YEAR - results['birth_year'],
        'Género': results['gender'].map({'F': 'F', 'M': 'M'}),
        'Dirección': results['address'],
        'Localidad': results['localidad_nombre']
    })
    
    # Create PDF buffer
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create the table data
    data = [export_df.columns.tolist()] + export_df.values.tolist()
    
    # Create table
    table = Table(data)
    
    # Add style to table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])
    table.setStyle(style)
    
    # Create the PDF
    elements = []
    
    # Add title
    title = Paragraph("Resultados de búsqueda", styles['Heading1'])
    elements.append(title)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Reset buffer position
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'votantes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True) 