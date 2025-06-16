from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .serializers import CustomUserSerializer, CreatorSerializer, PostSerializer, ProfileSerializer, SubscriptionSerializer, NotificationSerializer
from django.conf import settings
from .models import Post, CustomUser, Subscription, SubscriptionPlan, Notification
from rest_framework.exceptions import PermissionDenied
from .permissions import IsCreator
import stripe
import os
from django.views.generic import TemplateView
from django.core.mail import send_mail
# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['GET'])
def home(request):
    return Response("home")

class NotificationsListUpdateView(APIView):
    def get(self, request):
        read_all = request.query_params.get('read_all', 'false').lower() in ['true', 't', '1']
        only_count = request.query_params.get('only_count', 'false').lower() in ['true', 't', ] #HTTP polling
        notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
        if not read_all:
            #default behavior
            notifications = notifications.filter(is_read=False)
        if only_count:
            return  Response({"count": notifications.count()}, status=status.HTTP_200_OK)       
        serializer = NotificationSerializer(notifications, many=True)
        return Response({"count": len(serializer.data), "notifications":serializer.data}, status=status.HTTP_200_OK)
    def post(self, request):
        #read all
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message":f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)

class NotificationRetrieveUpdateView(APIView):
    def get(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        if notification.is_read:
            return Response({"error":"You already marked this notification as read"}, status=status.HTTP_400_BAD_REQUEST)
        notification.is_read = True
        notification.save()
        return Response({"message":f"You marked this notification as read, id: {id}"})

class MySubscriptionsView(APIView):
    def get(self, request):
        subscriptions = request.user.subscriptions.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, username):
        profile = get_object_or_404(CustomUser, username=username)
        is_subscribed = Subscription.objects.filter(creator=profile, subscriber=request.user).exists()
        serializer = ProfileSerializer(profile, context={'is_subscribed': is_subscribed, 'my_page': profile.id == request.user.id, "request":request,}) 
        return Response({"profile":serializer.data, "my_page": profile.id == request.user.id, "is_subscribed": is_subscribed})

class PostReportLikeView(APIView):
    def get_post(self, id):
        post = get_object_or_404(Post, id=id)
        if post.author == self.request.user:
            return post
        try:
            subscription = Subscription.objects.get(creator=post.author, subscriber=self.request.user)
        except Subscription.DoesNotExist:
            raise PermissionDenied("You are not subscribed!")
        
        if not subscription.is_active:
            raise PermissionDenied("Your subscription is not active!")
        return post
    def post(self, request, id):
        #report the post
        post = self.get_post(id=id)
        if post.author == request.user:
            return Response({"error": "You cannot report your own post"}, status=status.HTTP_400_BAD_REQUEST)
        if post.reports.filter(id=request.user.id).exists():
            return Response({"error": "You already reported this post"}, status=status.HTTP_400_BAD_REQUEST)
        post.reports.add(request.user)
        return Response({"message":"You reported the post"}, status=status.HTTP_201_CREATED)
    def put(self, request, id):
        #like/unlike the post
        post = self.get_post(id=id)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            Notification.objects.filter(
                user=post.author,
                fromuser=request.user,
                category='like',
                related_post=post
                ).delete()
            return Response({"message":"You unliked the post"}, status=status.HTTP_200_OK)
        else:
            post.likes.add(request.user)
            Notification.objects.create(
            user=post.author,
            fromuser=request.user,
            category='like',
            message= f'{request.user.username} liked the post: "{post.title[:10]}"',
            related_post=post
            )
            return Response({"message":"You liked the post"}, status=status.HTTP_200_OK)

class CreatorDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCreator]
    def get(self, request):
        #receive info to view or edit
        serializer = CreatorSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request):
        #update creator
        serializer = CreatorSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)    
class PostCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCreator]
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response({"message":"You successfully created a post!"}, status=status.HTTP_201_CREATED)
class PostDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCreator]
    def get_post(self, pk):
        post = get_object_or_404(Post, id=pk)
        if self.request.user != post.author:
            raise PermissionDenied("This is not your post!") #403
        return post
    def get(self, request, pk):
        post = self.get_post(pk=pk)
        serializer = PostSerializer(post, context={"request":request}) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request, pk):
        post = self.get_post(pk=pk)
        serializer = PostSerializer(instance=post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True) 
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK) 
    def delete(self, request, pk):
        post = self.get_post(pk=pk)
        post_title = post.title    
        post.delete()
        return Response({"message":f"Post '{post_title}' is deleted"}, status=status.HTTP_200_OK)

#STRIPE below
class CreatorBecomeStripeView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if SubscriptionPlan.objects.filter(creator=request.user).exists():
            return Response({"error":"You already a creator!"}, status=status.HTTP_400_BAD_REQUEST)
        price = request.data.get('price')
        greeting_message = request.data.get('greeting_message')
        # print(price)
        # print(greeting_message)
        if not price or not greeting_message:
            return Response({"error":"Both Price and Greeting message fields are required!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            price = int(price)
        except ValueError:
            return Response({"error": "Price must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        name = f'Subscription Plan for {request.user.username}'
        try:
            stripe_price = stripe.Price.create(
                unit_amount=int(price * 100),
                currency="usd",
                recurring={"interval": "month"},
                product_data={"name": name}
            )
            # create in the db
            subscription = SubscriptionPlan.objects.create(
                creator=request.user,
                price=price*100,
                stripe_price_id=stripe_price.id,
                greeting_message = greeting_message
            )
            user = request.user
            user.is_creator = True
            user.save()
            return Response({
                'message': 'Subscription plan created successfully',
                'subscription_id': subscription.stripe_price_id,
                'stripe_price_id': stripe_price.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"error":"Server Error"}, status=500)  

class CheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        username = request.data.get("username")
        creator = get_object_or_404(CustomUser, username=username)
        user = request.user
        YOUR_DOMAIN = os.environ.get("YOUR_DOMAIN")
        stripe_price_id = None
        if Subscription.objects.filter(creator=creator, subscriber=user).exists():
            return Response({"error":"You already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(creator, 'subscription_plan') and creator.subscription_plan:
            stripe_price_id = creator.subscription_plan.stripe_price_id
        else:
            return Response({"error":"No subscription plan for this user"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': stripe_price_id,
                        'quantity': 1,
                    },
                ],
                metadata={
                "creator": creator.username,
                "subscriber": user.username 
                },
                mode='subscription',
                success_url=YOUR_DOMAIN +
                f'success/',
                cancel_url=YOUR_DOMAIN + 'cancel/',
            )
            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)  
class SuccessView(TemplateView):
    template_name = 'success.html'
class CancelView(TemplateView):
    template_name = 'cancel.html'

class SubscriptionCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        creator_username = request.data.get("username", "")
        creator = get_object_or_404(CustomUser, username=creator_username)
        user = request.user
        subscription = Subscription.objects.filter(creator=creator, subscriber=user).first()
        if not subscription:
            return Response({"error":"No such subscription"}, status=status.HTTP_400_BAD_REQUEST)
        stripe.Subscription.cancel(subscription.stripe_subscription_id)    
        # subscription.is_active = False
        # subscription.save()
        return Response({"response":"Subscription was cancelled!"})    
       
@csrf_exempt
def stripe_webhook(request):
    print("WEBHOOK -----------------------------------------------------")
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    event_type = event['type']
    session = event['data']['object']
    
    metadata = session["metadata"]
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        # Access the metadata from the session
        creator_username = session['metadata']['creator']
        subscriber_username = session['metadata']['subscriber']
        # Retrieve Subscription ID from the session
        subscription_id = session.get('subscription') 
        customer_details = session.get('customer_details')
        # print(customer_details)
        # print(customer_details['email'])
        # print(subscription_id)
        # Process the metadata and other session information
        print(f"Creator: {creator_username}, Subscriber: {subscriber_username}")
        creator = get_object_or_404(CustomUser, username=creator_username)
        subscriber = get_object_or_404(CustomUser, username=subscriber_username)
        new_subscription = Subscription(creator=creator, subscriber=subscriber, stripe_subscription_id=subscription_id)
        new_subscription.save()
        print("Subscription was created!")
        subscriber_email=customer_details['email']
        try:
            send_mail(
                subject='Greeting Message',
                message=creator.subscription_plan.greeting_message,
                from_email=os.environ.get("EMAIL_HOST_USER"),
                recipient_list=[subscriber_email]
            )
        except Exception as e:
            print(f"Failed to send greeting email: {e}")
        #TODO send a notification to the creator
        Notification.objects.create(
            user=creator,
            fromuser=subscriber,
            category='subscription',
            message=f'Hooray! {subscriber.username} subscribed on you!'
        )
        #maybe send for analytics
        return HttpResponse(status=201)
    elif event_type == 'customer.subscription.trial_will_end':
        # send email probably
        print('Subscription trial will end')
    elif event_type == 'customer.subscription.deleted':
        subscription_id = event['data']['object']['id']
        # Subscription.objects.filter(stripe_subscription_id=subscription_id).update(is_active=False)
        sub = get_object_or_404(Subscription, stripe_subscription_id=subscription_id)
        sub.delete()
        print("Subscription was deleted!")
        #TODO BYE BYE EMAIL
        subscriber_email = "???"
        # send_mail(subject='Goodbye Message',
        #         message="We are sad to hear that you are leaving!",
        #         from_email=os.environ.get("EMAIL_HOST_USER"),
        #         recipient_list=[subscriber_email])
        #maybe send for analytics
        # return HttpResponse(status=200)
    return HttpResponse(status=200)


# Authentication below #
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"You successfully created an account!"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class LoginLogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"error":"username and password are required fields!"}, status=status.HTTP_400_BAD_REQUEST)
        user =  authenticate(username=username, password=password)   
        if not user or not user.is_active:
            return Response({"error": "Invalid credentials or inactive account"}, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        response = Response({
            "message":"You logged in!", "username": user.username, "is_creator": user.is_creator
            }, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age= settings.ACCESS_TOKEN_LIFETIME,
            secure=True,
            httponly=True,
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age= settings.REFRESH_TOKEN_LIFETIME,
            secure=True,
            httponly=True,
            samesite="Lax"
        )  
        return response
    def delete(self, request):
        refresh = request.COOKIES.get("refresh_token")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass  # Можно логировать или просто игнорировать

        response = Response({"message":"You logged out!"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    
class RefreshView(APIView):
    permission_classes=[AllowAny]

    def get(self, request):
        # no access token at this time (Anonymous user)
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error":"No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_refresh_token = RefreshToken(refresh_token)
            new_access_token=str(new_refresh_token.access_token)
            response = Response({"message":"Server refreshed your access token"}, status=status.HTTP_200_OK)
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                secure=True,
                httponly=True,
                samesite='Lax',
                max_age=settings.ACCESS_TOKEN_LIFETIME

            )
            return response
        except (TokenError, InvalidToken):
            response = Response({"error":"Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
        
class UserCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user and request.user.is_authenticated:
            return Response({"username":request.user.username,"is_creator":request.user.is_creator, "authenticated":True}, status=status.HTTP_200_OK)
        else:
            return Response({"username":"", "is_creator":False, "authenticated":False}, status=status.HTTP_200_OK)
#            