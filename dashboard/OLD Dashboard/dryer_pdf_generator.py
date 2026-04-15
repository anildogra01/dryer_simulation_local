"""
PDF Report Generator for Grain Dryer Simulation
Creates professional reports with graphs and tables
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import io

class DryerReportGenerator:
    """Generate PDF reports with user header, tables, and graphs"""
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.doc = SimpleDocTemplate(output_path, pagesize=letter,
                                     topMargin=0.5*inch, bottomMargin=0.5*inch,
                                     leftMargin=0.75*inch, rightMargin=0.75*inch)
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a5490'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            alignment=TA_LEFT
        )
    
    def add_header(self, user_info, simulation_date):
        """Add user information header"""
        # Title
        title = Paragraph("<b>GRAIN DRYER SIMULATION REPORT</b>", self.title_style)
        self.story.append(title)
        self.story.append(Spacer(1, 0.2*inch))
        
        # User information table
        header_data = [
            ['User:', user_info.get('user_name', 'N/A')],
            ['Project:', user_info.get('project_name', 'N/A')],
            ['Address:', user_info.get('address', 'N/A')],
            ['Date:', simulation_date]
        ]
        
        header_table = Table(header_data, colWidths=[1.5*inch, 5*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        self.story.append(header_table)
        self.story.append(Spacer(1, 0.3*inch))
        
        # Horizontal line
        from reportlab.platypus import HRFlowable
        self.story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a5490')))
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_input_summary(self, input_params, crop_name):
        """Add input parameters summary table"""
        section_title = Paragraph("<b>INPUT PARAMETERS</b>", self.styles['Heading2'])
        self.story.append(section_title)
        self.story.append(Spacer(1, 0.1*inch))
        
        # Input parameters table
        data = [
            ['Parameter', 'Value', 'Units'],
            ['Crop Type', crop_name, ''],
            ['Initial Moisture', f"{input_params.get('initial_moisture', 'N/A'):.1f}", '%'],
            ['Grain Temperature', f"{input_params.get('grain_temp', 'N/A'):.1f}", '°F'],
            ['Air Temperature', f"{input_params.get('air_temp', 'N/A'):.1f}", '°F'],
            ['Relative Humidity', f"{input_params.get('rel_humidity', 'N/A'):.1f}", '%'],
            ['Air Flow Rate', f"{input_params.get('air_flow_cfm', 'N/A'):.1f}", 'CFM'],
            ['Bed Depth', f"{input_params.get('bed_depth', 'N/A'):.1f}", 'ft'],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_results_summary(self, summary):
        """Add results summary table"""
        section_title = Paragraph("<b>SIMULATION RESULTS</b>", self.styles['Heading2'])
        self.story.append(section_title)
        self.story.append(Spacer(1, 0.1*inch))
        
        # Results table
        data = [
            ['Result', 'Value', 'Units'],
            ['Final Moisture', f"{summary.get('final_moisture_pct', 'N/A'):.2f}", '%'],
            ['Moisture Removed', f"{summary.get('moisture_removed_pct', 'N/A'):.2f}", '% points'],
            ['Total Drying Time', f"{summary.get('total_time_hr', 'N/A'):.2f}", 'hours'],
            ['Total Energy Used', f"{summary.get('total_energy_btu', 'N/A'):.2f}", 'BTU'],
            ['Water Removed', f"{summary.get('total_water_removed_lb', 'N/A'):.2f}", 'lb'],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d7a3e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_moisture_graph(self, time_series):
        """Add moisture vs time graph"""
        if not time_series:
            return
        
        section_title = Paragraph("<b>MOISTURE CONTENT vs TIME</b>", self.styles['Heading2'])
        self.story.append(section_title)
        self.story.append(Spacer(1, 0.1*inch))
        
        # Extract data
        times = [point['time_hr'] for point in time_series]
        moistures = [point['avg_moisture_pct'] for point in time_series]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(times, moistures, 'b-o', linewidth=2, markersize=6)
        ax.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Moisture Content (%)', fontsize=11, fontweight='bold')
        ax.set_title('Drying Curve', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Add to PDF
        img = Image(img_buffer, width=5.5*inch, height=3.7*inch)
        self.story.append(img)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_temperature_graph(self, time_series):
        """Add temperature profile graph"""
        if not time_series or not time_series[0].get('temp_profile'):
            return
        
        section_title = Paragraph("<b>TEMPERATURE PROFILE</b>", self.styles['Heading2'])
        self.story.append(section_title)
        self.story.append(Spacer(1, 0.1*inch))
        
        # Plot final temperature profile
        last_point = time_series[-1]
        temp_profile = last_point.get('temp_profile', [])
        
        if temp_profile:
            depths = list(range(len(temp_profile)))
            
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(depths, temp_profile, 'r-o', linewidth=2, markersize=6)
            ax.set_xlabel('Position (nodes)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Temperature (°F)', fontsize=11, fontweight='bold')
            ax.set_title(f'Temperature Profile at t={last_point["time_hr"]:.1f} hr', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Add to PDF
            img = Image(img_buffer, width=5.5*inch, height=3.7*inch)
            self.story.append(img)
    
    def generate(self, user_info, crop_name, parsed_data):
        """Generate the complete PDF report"""
        # Header with user info
        simulation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.add_header(user_info, simulation_date)
        
        # Input parameters
        self.add_input_summary(parsed_data.get('input_params', {}), crop_name)
        
        # Results summary
        self.add_results_summary(parsed_data.get('summary', {}))
        
        # Graphs
        time_series = parsed_data.get('time_series', [])
        if time_series:
            self.add_moisture_graph(time_series)
            self.add_temperature_graph(time_series)
        
        # Build PDF
        self.doc.build(self.story)
        print(f"✅ PDF report generated: {self.output_path}")


if __name__ == '__main__':
    # Test
    test_user_info = {
        'user_name': 'John Doe',
        'project_name': 'Test Farm Dryer Project',
        'address': '123 Farm Road, Henrietta, NY'
    }
    
    test_data = {
        'input_params': {
            'initial_moisture': 25.0,
            'grain_temp': 70.0,
            'air_temp': 110.0,
            'rel_humidity': 30.0,
            'air_flow_cfm': 500.0,
            'bed_depth': 5.0
        },
        'summary': {
            'final_moisture_pct': 17.5,
            'moisture_removed_pct': 7.5,
            'total_time_hr': 12.0,
            'total_energy_btu': 5000.0,
            'total_water_removed_lb': 25.0
        },
        'time_series': [
            {'time_hr': 0.0, 'avg_moisture_pct': 25.0},
            {'time_hr': 2.0, 'avg_moisture_pct': 23.0},
            {'time_hr': 4.0, 'avg_moisture_pct': 21.0},
            {'time_hr': 6.0, 'avg_moisture_pct': 19.5},
            {'time_hr': 8.0, 'avg_moisture_pct': 18.5},
            {'time_hr': 10.0, 'avg_moisture_pct': 17.8},
            {'time_hr': 12.0, 'avg_moisture_pct': 17.5, 'temp_profile': [110, 95, 85, 75, 70]},
        ]
    }
    
    generator = DryerReportGenerator('test_report.pdf')
    generator.generate(test_user_info, 'Corn', test_data)
    print("Test PDF created!")
