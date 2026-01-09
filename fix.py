# fix_restaurants_function.py
import re

with open('app/admin.py', 'r') as f:
    content = f.read()

# The correct manage_restaurants function
correct_manage_restaurants = '''@admin_bp.route('/restaurants')
@login_required
@admin_required
def manage_restaurants():
    restaurants = Restaurant.query.all()
    
    restaurants_with_stats = []
    for restaurant in restaurants:
        orders_count = Order.query.filter_by(restaurant_id=restaurant.restaurant_id).count()
        total_revenue = db.session.query(func.sum(Order.total_amount))\\
            .filter(Order.restaurant_id == restaurant.restaurant_id)\\
            .scalar() or 0
        
        restaurants_with_stats.append({
            'restaurant': restaurant,
            'orders_count': orders_count,
            'total_revenue': total_revenue,
            'is_active': restaurant.is_active,
            'is_open': restaurant.is_open
        })
    
    return render_template('admin/manage_restaurants.html',
                         restaurants=restaurants_with_stats)
'''

# Find and replace the broken function
# We need to find from "@admin_bp.route('/restaurants')" to just before "@admin_bp.route('/system/health')"
pattern = r'(@admin_bp\.route\(\'/restaurants\'\)\s*\n@login_required\s*\n@admin_required\s*\ndef manage_restaurants\(\):.*?)(?=\s*@admin_bp\.route\(\'/system/health\'\)|\s*def system_health\(\):)'

# Replace with correct function
new_content = re.sub(pattern, correct_manage_restaurants, content, flags=re.DOTALL)

with open('app/admin.py', 'w') as f:
    f.write(new_content)

print("Fixed manage_restaurants function!")
