# fix_all_template_links.py
import re

with open('app/templates/admin/base_dashboard.html', 'r') as f:
    content = f.read()

# Dictionary of broken links and their fixes
# If the endpoint doesn't exist, we either:
# 1. Redirect to a working endpoint
# 2. Disable the link
link_fixes = {
    "url_for('admin.manage_users')": "url_for('admin.manage_customers')",
    "url_for('admin.manage_reviews')": "url_for('admin.dashboard')",  # or "#" to disable
    "url_for('admin.manage_promotions')": "url_for('admin.dashboard')",
    "url_for('admin.manage_analytics')": "url_for('admin.dashboard')",
    "url_for('admin.manage_settings')": "url_for('admin.dashboard')",
    "url_for('admin.manage_notifications')": "url_for('admin.dashboard')",
    "url_for('admin.manage_help')": "url_for('admin.dashboard')",
}

for broken, fixed in link_fixes.items():
    content = content.replace(broken, fixed)

# Save the fixed template
with open('app/templates/admin/base_dashboard.html', 'w') as f:
    f.write(content)

print("Fixed all template links!")
