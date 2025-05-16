from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('accounts/register/', views.RegisterView.as_view()),
    path('accounts/login_logout/', views.LoginLogoutView.as_view()),
    path('accounts/refresh_token/', views.RefreshView.as_view()),
    path('accounts/me/', views.UserCheckView.as_view()),
]
