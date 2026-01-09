# check_routes.py
from app import create_app

app = create_app()

print("🔍 Registered routes:")
print("="*50)
for rule in app.url_map.iter_rules():
    if 'api' in rule.rule or 'API' in str(rule):
        print(f"{rule.rule:40} {rule.endpoint:30} {list(rule.methods)}")

print("\n📋 All routes:")
print("="*50)
count = 0
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if count < 20:  # Show first 20
        print(f"{rule.rule:40} {rule.endpoint:30} {list(rule.methods)}")
        count += 1
