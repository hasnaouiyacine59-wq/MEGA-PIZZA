import re

# Read the file
with open('app/admin.py', 'r') as f:
    lines = f.readlines()

# Find where manage_restaurants ends and system_health begins
start_line = -1
end_line = -1
in_duplicate_section = False

for i, line in enumerate(lines):
    if 'def manage_restaurants():' in line:
        start_line = i
    elif 'def system_health():' in line and start_line != -1:
        end_line = i
        break

# If we found a duplicate section, remove it
if start_line != -1 and end_line != -1:
    # Keep everything up to manage_restaurants
    new_lines = lines[:start_line + 5]  # +5 to keep the manage_restaurants function
    
    # Find system_health and keep from there
    for i in range(end_line, len(lines)):
        new_lines.append(lines[i])
    
    # Write back
    with open('app/admin.py', 'w') as f:
        f.writelines(new_lines)
    print("Fixed! Removed duplicate placeholder routes.")
else:
    print("No duplicate section found. Trying alternative fix...")
    
    # Alternative: just ensure we only have one set of placeholders
    # Count how many times each placeholder appears
    endpoints = ['/users', '/reviews', '/promotions', '/analytics', '/settings', '/notifications', '/help']
    for endpoint in endpoints:
        count = sum(1 for line in lines if f"@admin_bp.route('{endpoint}')" in line)
        if count > 1:
            print(f"Warning: {endpoint} appears {count} times")
