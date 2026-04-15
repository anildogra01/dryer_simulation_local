"""
FIXED.OUT Parser
Extracts tables, curves, and summary data from Fortran output
"""

import re
from datetime import datetime

class FixedOutParser:
    """Parse FIXED.OUT file to extract simulation results"""
    
    def __init__(self, output_file_path):
        self.output_file = output_file_path
        with open(output_file_path, 'r') as f:
            self.content = f.read()
        
        self.data = {
            'input_params': {},
            'time_series': [],
            'summary': {},
            'success': False
        }
    
    def parse(self):
        """Parse the entire output file"""
        try:
            self._parse_input_params()
            self._parse_time_series()
            self._parse_summary()
            self.data['success'] = True
            return self.data
        except Exception as e:
            print(f"Error parsing FIXED.OUT: {e}")
            self.data['error'] = str(e)
            return self.data
    
    def _parse_input_params(self):
        """Extract input parameters from header"""
        # Air temperature
        match = re.search(r'AIR TEMP\(DEG F\).*?\n\s+([\d.]+)', self.content)
        if match:
            self.data['input_params']['air_temp'] = float(match.group(1))
        
        # Product temperature
        match = re.search(r'PROD TEMP\(DEG F\).*?\n\s+[\d.]+\s+([\d.]+)', self.content)
        if match:
            self.data['input_params']['grain_temp'] = float(match.group(1))
        
        # Relative humidity
        match = re.search(r'REL HUM\(DECIMAL\).*?\n\s+[\d.]+\s+[\d.]+\s+([\d.]+)', self.content)
        if match:
            self.data['input_params']['rel_humidity'] = float(match.group(1)) * 100  # Convert to %
        
        # Initial moisture
        match = re.search(r'DB MC\(DECIMAL\).*?\n\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)', self.content)
        if match:
            self.data['input_params']['initial_moisture'] = float(match.group(1)) * 100  # Convert to %
        
        # Air flow rate
        match = re.search(r'AIR FLOW RATE \(CFM\)\s*\n\s+([\d.]+)', self.content)
        if match:
            self.data['input_params']['air_flow_cfm'] = float(match.group(1))
        
        # Bed depth
        match = re.search(r'SIMULATE A DEPTH OF\s+([\d.]+)\s+FT', self.content)
        if match:
            self.data['input_params']['bed_depth'] = float(match.group(1))
    
    def _parse_time_series(self):
        """Extract time series data (moisture, temperature over time)"""
        # Find all time blocks (TIME = X.XX)
        time_blocks = re.finditer(r'0TIME =\s+([\d.]+).*?AVERAGE MC =([\d.]+).*?ENERGY INPUT =\s+([\d.]+).*?H20 REMOVED =\s+([\d.]+)', 
                                   self.content, re.DOTALL)
        
        for block in time_blocks:
            time_hr = float(block.group(1))
            avg_moisture = float(block.group(2)) * 100  # Convert to %
            energy_input = float(block.group(3))
            water_removed = float(block.group(4))
            
            # Find the moisture profile line after this time block
            # Look for: 0MC DB  0.175   0.250   0.250   0.250   0.250
            mc_match = re.search(r'0MC DB\s+([\d.\s]+)', self.content[block.end():block.end()+500])
            moisture_profile = []
            if mc_match:
                mc_values = mc_match.group(1).split()
                moisture_profile = [float(x) * 100 for x in mc_values]  # Convert to %
            
            # Find temperature profile
            # Look for: 0PROD TEMP 90.000  70.000  70.000  70.000  70.000
            temp_match = re.search(r'0PROD TEMP\s+([\d.\s]+)', self.content[block.end():block.end()+500])
            temp_profile = []
            if temp_match:
                temp_values = temp_match.group(1).split()
                temp_profile = [float(x) for x in temp_values]
            
            self.data['time_series'].append({
                'time_hr': time_hr,
                'avg_moisture_pct': avg_moisture,
                'energy_btu': energy_input,
                'water_removed_lb': water_removed,
                'moisture_profile': moisture_profile,
                'temp_profile': temp_profile
            })
    
    def _parse_summary(self):
        """Extract summary statistics"""
        if self.data['time_series']:
            # Final values from last time step
            last_point = self.data['time_series'][-1]
            self.data['summary']['final_moisture_pct'] = last_point['avg_moisture_pct']
            self.data['summary']['total_time_hr'] = last_point['time_hr']
            self.data['summary']['total_energy_btu'] = last_point['energy_btu']
            self.data['summary']['total_water_removed_lb'] = last_point['water_removed_lb']
            
            # Initial moisture from first time step
            if self.data['time_series']:
                first_point = self.data['time_series'][0]
                self.data['summary']['initial_moisture_pct'] = first_point['avg_moisture_pct']
                
                # Calculate moisture removal
                moisture_removed = first_point['avg_moisture_pct'] - last_point['avg_moisture_pct']
                self.data['summary']['moisture_removed_pct'] = moisture_removed


if __name__ == '__main__':
    # Test
    import sys
    if len(sys.argv) > 1:
        parser = FixedOutParser(sys.argv[1])
        data = parser.parse()
        
        print("="*70)
        print("PARSED DATA")
        print("="*70)
        print(f"\nInput Parameters: {data['input_params']}")
        print(f"\nTime Series Points: {len(data['time_series'])}")
        print(f"\nSummary: {data['summary']}")
        print(f"\nSuccess: {data['success']}")
    else:
        print("Usage: python fixed_out_parser.py <path_to_FIXED.OUT>")
