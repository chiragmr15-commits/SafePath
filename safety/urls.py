from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/',
         views.dashboard,
         name='dashboard'),

    path('profile/',
         views.profile_view,
         name='profile'),

    path('settings/',
         views.settings_view,
         name='settings'),

    path('navigation/',
         views.navigation,
         name='navigation'),

    path('safety-zones/',
         views.safety_zones,
         name='safety_zones'),

    path('guardian/',
         views.guardian,
         name='guardian'),

    path('reports/',
         views.reports,
         name='reports'),
    
    path('emergency-contacts/',
         views.emergency_contacts,
         name='emergency_contacts'),
    
    path('api/zones/', views.api_zones, name='api_zones'),
    path('api/report/', views.api_report, name='api_report'),
    
    # Community Reports API
    path('api/reports/', views.api_community_reports, name='api_community_reports'),
    path('api/reports/<int:report_id>/', views.api_community_report_detail, name='api_community_report_detail'),
    
    # Route Analysis API
    path('api/route-analysis/', views.api_route_analysis, name='api_route_analysis'),
    path('api/route-geometry/', views.api_route_geometry, name='api_route_geometry'),
    
    # Location Search API
    path('api/location-search/', views.api_location_search, name='api_location_search'),
    path('api/reverse-geocode/', views.api_reverse_geocode, name='api_reverse_geocode'),
    
    # Safety Intelligence Center API
    path('api/safety-heatmap/', views.api_safety_heatmap, name='api_safety_heatmap'),
    path('api/area-safety-score/', views.api_area_safety_score, name='api_area_safety_score'),
    path('api/time-based-safety/', views.api_time_based_safety, name='api_time_based_safety'),
    path('api/safe-places/', views.api_safe_places, name='api_safe_places'),
    path('api/dangerous-areas/', views.api_dangerous_areas, name='api_dangerous_areas'),
    path('api/safety-trends/', views.api_safety_trends, name='api_safety_trends'),
    
    # Emergency Contacts API
    path('api/emergency-contacts/', views.api_emergency_contacts, name='api_emergency_contacts'),
    path('api/emergency-contacts/<int:contact_id>/', views.api_emergency_contact_detail, name='api_emergency_contact_detail'),
    
    # User Preferences API
    path('api/user-preferences/', views.api_user_preferences, name='api_user_preferences'),
    
    # Community Reports Statistics & AI Recommendations
    path('api/reports-statistics/', views.api_reports_statistics, name='api_reports_statistics'),
    path('api/ai-recommendations/', views.api_ai_recommendations, name='api_ai_recommendations'),
    
    # SOS API
    path('api/send-sos/', views.api_send_sos, name='api_send_sos'),
    path('api/sos-history/', views.api_sos_history, name='api_sos_history'),
    
    # Route History API
    path('api/route-history/', views.api_route_history, name='api_route_history'),
]