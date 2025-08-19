# records/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .views import (
    dashboard, settings_view,
    PersonListView, PersonCreateView, PersonUpdateView, PersonDeleteView, PersonDetailView,
    RequestListView, RequestDetailView, RequestCreateView, RequestUpdateView, RequestDeleteView,
    RegionalUnitsAPIView, MunicipalitiesAPIView, QuickSearchAPIView, statistics_view
)

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path("register/", views.register, name="register"),
    
    # Dashboard and main pages
    path('', views.dashboard, name='dashboard'),
    path('statistics/', statistics_view, name='statistics'),
    path('settings/', settings_view, name='settings_view'),
    
    # Person management
    path("persons/", PersonListView.as_view(), name="person_list"),
    path("persons/new/", PersonCreateView.as_view(), name="person_create"),
    path("persons/<int:pk>/", PersonDetailView.as_view(), name="person_detail"),  # Added missing detail view
    path("persons/<int:pk>/edit/", PersonUpdateView.as_view(), name="person_update"),
    path("persons/<int:pk>/delete/", PersonDeleteView.as_view(), name="person_delete"),
    
    # Request management
    path("requests/", RequestListView.as_view(), name="request_list"),
    path("requests/new/", RequestCreateView.as_view(), name="request_create"),
    path("requests/<int:pk>/", RequestDetailView.as_view(), name="request_detail"),
    path("requests/<int:pk>/edit/", RequestUpdateView.as_view(), name="request_update"),
    path("requests/<int:pk>/delete/", RequestDeleteView.as_view(), name="request_delete"),
    
    # API endpoints for AJAX functionality
    path('api/regional-units/', RegionalUnitsAPIView.as_view(), name='api_regional_units'),
    path('api/municipalities/', MunicipalitiesAPIView.as_view(), name='api_municipalities'),
    path('api/quick-search/', QuickSearchAPIView.as_view(), name='api_quick_search'),
]