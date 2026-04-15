# Read the file
with open('dryer_dashboard_pythonanywhere.py', 'r') as f:
    lines = f.readlines()

# Find all occurrences of get_all_crops_api
occurrences = []
for i, line in enumerate(lines):
    if 'def get_all_crops_api():' in line:
        occurrences.append(i)

print(f"Found {len(occurrences)} occurrences at lines: {[o+1 for o in occurrences]}")

# Keep only the FIRST occurrence (inside create_app function)
# Remove all others
if len(occurrences) > 1:
    # Work backwards to preserve line numbers
    for occurrence in reversed(occurrences[1:]):
        # Find the end of this function (next def or end of section)
        end_line = occurrence + 1
        while end_line < len(lines):
            line = lines[end_line].strip()
            # Stop at next function or decorator or major section
            if (line.startswith('def ') or 
                line.startswith('@app') or 
                line.startswith('# ===') or
                (line.startswith('application =') and 'create_app' in line)):
                break
            end_line += 1
        
        # Remove this duplicate block
        print(f"Removing duplicate at lines {occurrence+1} to {end_line}")
        del lines[occurrence:end_line]

# Write back
with open('dryer_dashboard_pythonanywhere.py', 'w') as f:
    f.writelines(lines)

print("✅ Duplicates removed!")
