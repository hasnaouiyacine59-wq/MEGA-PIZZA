
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Mega Pizza Admin{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Base Admin CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin/base.css') }}">
    
    <!-- Components CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin/components.css') }}">
    
    {% block styles %}{% endblock %}
</head>
<body>
    <!-- Top Navigation -->
    <nav class="navbar navbar-admin navbar-expand-lg">
        <div class="container-fluid">
            <button class="sidebar-toggle" id="sidebarToggle">
                <i class="fas fa-bars"></i>
            </button>
            
            <a class="navbar-brand" href="{{ url_for('main.index') }}">
                <i class="fas fa-pizza-slice me-2"></i>Mega Pizza Admin
            </a>
            
            <div class="navbar-nav ms-auto">
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                        <i class="fas fa-user-circle me-1"></i> {{ current_user.username }}
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="#"><i class="fas fa-user me-2"></i>Profile</a></li>
                        <li><a class="dropdown-item" href="#"><i class="fas fa-cog me-2"></i>Settings</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </nav>

    <!-- Dashboard Layout Wrapper -->
    <div class="dashboard-wrapper">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap 5 JS Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Base Admin JS -->
    <script src="{{ url_for('static', filename='js/admin/base.js') }}"></script>
    
    <!-- Custom Scripts -->
    {% block scripts %}{% endblock %}
</body>
</html>