# Read the file
with open('dryer_dashboard_pythonanywhere.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find the create_app function boundaries
create_app_start = None
create_app_end = None

for i, line in enumerate(lines):
    if 'def create_app(' in line:
        create_app_start = i
    if create_app_start and line.strip() == 'return app':
        create_app_end = i
        break

print(f"create_app function: lines {create_app_start+1} to {create_app_end+1}")

# Keep only API routes INSIDE create_app (between start and first 'return app')
# Remove everything else related to crop master routes

clean_lines = []
in_crop_section = False
skip_line = False

for i, line in enumerate(lines):
    # Skip crop master sections outside create_app
    if i < create_app_start or i > create_app_end:
        if '# CROP MASTER API ENDPOINTS' in line:
            in_crop_section = True
            continue
        
        if in_crop_section:
            # Skip until we hit a major section or application creation
            if line.startswith('application =') or line.startswith('if __name__'):
                in_crop_section = False
            else:
                continue
    
    clean_lines.append(line)

# Write back
with open('dryer_dashboard_pythonanywhere.py', 'w') as f:
    f.write('\n'.join(clean_lines))

print("✅ Thorough cleanup complete!")
