from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    #authentication 👇
    path('accounts/register/', views.RegisterView.as_view()),
    path('accounts/login_logout/', views.LoginLogoutView.as_view()), #GET TOKENS, GET RID OF THEM
    path('accounts/refresh_token/', views.RefreshView.as_view()),
    path('accounts/me/', views.UserCheckView.as_view()), #GIVE INFO TO THE FRONTEND ABOUT USER
    #creator 👇
    path('creator/', views.CreatorView.as_view()), #GET INFO, BECOME A CREATOR, EDIT CREATOR
]
