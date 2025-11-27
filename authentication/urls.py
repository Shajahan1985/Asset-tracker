from django.urls import path
from .views import (
    LoginView, LogoutView, dashboard_view,
    UserListView, UserCreateView, UserUpdateView,
    user_deactivate, user_reactivate
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # User management URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/deactivate/', user_deactivate, name='user_deactivate'),
    path('users/<int:pk>/reactivate/', user_reactivate, name='user_reactivate'),
]
