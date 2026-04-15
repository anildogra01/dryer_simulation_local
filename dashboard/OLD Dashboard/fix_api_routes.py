# Read the file
with open('dryer_dashboard_pythonanywhere.py', 'r') as f:
    content = f.read()

# Remove the incorrectly placed API routes
lines = content.split('\n')
new_lines = []
skip_until_next_section = False

for i, line in enumerate(lines):
    # Skip the API routes section we added incorrectly
    if '# CROP MASTER API ENDPOINTS' in line:
        skip_until_next_section = True
        continue
    
    if skip_until_next_section:
        # Skip until we find a non-route line
        if not line.strip().startswith('@app') and not line.strip().startswith('def ') and not line.strip().startswith("'''") and not line.strip().startswith('try:') and not line.strip().startswith('crops') and not line.strip().startswith('return') and not line.strip().startswith('except') and line.strip() != '':
            skip_until_next_section = False
        else:
            continue
    
    new_lines.append(line)

# Write cleaned content
with open('dryer_dashboard_pythonanywhere.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Removed incorrectly placed routes")
