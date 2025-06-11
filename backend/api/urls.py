from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    #authentication 👇
    path('accounts/register/', views.RegisterView.as_view()),
    path('accounts/login_logout/', views.LoginLogoutView.as_view()), #get tokens, delete tokens
    path('accounts/refresh_token/', views.RefreshView.as_view()),
    path('accounts/me/', views.UserCheckView.as_view()), #give info to the frontend about the user
    #creator 👇
    path('creator/', views.CreatorDetailView.as_view()), #retrieve and update a creator
    path('creator/become/', views.CreatorBecomeStripeView.as_view()), #BECOME A CREATOR with stripe
    path('creator/posts/', views.PostCreateView.as_view()), #create post
    path('creator/posts/<int:pk>/', views.PostDetailView.as_view()), #retrieve, update, delete post

    path('posts/report_like/<int:id>/', views.PostReportLikeView.as_view()), #report(post), like/unlike (put) posts
    path('profile/<str:username>/', views.ProfileView.as_view()),
    path('my_subscriptions/', views.MySubscriptionsView.as_view()),
    #stripe block below
    path('subscribe/', views.CheckoutSessionView.as_view()),
    path('success/', views.SuccessView.as_view()), #html after successful payment
    path('cancel/', views.CancelView.as_view()), #html if error
    path('cancel_subscription/', views.SubscriptionCancelView.as_view()), 
    path('webhooks/stripe/', views.stripe_webhook)
]
