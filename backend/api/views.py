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
from .send_goodbye_email import send_goodbye_email
from django.utils import timezone
from datetime import datetime

class NotificationsMarkReadView(APIView):
    """
    API endpoint to mark notifications as read or unread.

    PUT:
    - Accepts a list of notification IDs and boolean flags 'mark_read' and 'mark_all'.
    - If 'mark_all' is True, marks all notifications as read for the user.
    - If 'mark_read' is True, marks provided notifications as read.
    - If 'mark_read' is False, marks provided notifications as unread.
    - Returns a message with the result of the operation.
    """
    def put(self, request):
        """
        Mark notifications as read or unread.

        Request body:
        - mark_read (bool): Mark as read (default True)
        - mark_all (bool): Mark all as read (default False)
        - ids (list): List of notification IDs

        Returns:
        - message: Result of the operation
        """
        mark_read = request.data.get("mark_read", True)
        mark_all = request.data.get("mark_all", False)
        ids = request.data.get("ids", [])
        if not isinstance(mark_read, bool) or not isinstance(mark_all, bool):
            return Response({"error":"mark_read and mark_all fields have to be booleans"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(ids, list):
            return Response({"error":"ids field have to be a list"}, status=status.HTTP_400_BAD_REQUEST)
        ids = [id for id in ids if isinstance(id, int) and not isinstance(id, bool)]
        if not mark_all and not ids:
            return Response({"error": "No notification IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        if mark_all:
            updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return Response({"message":f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)
        if mark_read:
            Notification.objects.filter(user=request.user, is_read=False, id__in=ids).update(is_read=True)
            return Response({"message":"marked as read"}, status=status.HTTP_200_OK)
        else:
            Notification.objects.filter(user=request.user, is_read=True, id__in=ids).update(is_read=False)
            return Response({"message":"marked as unread"}, status=status.HTTP_200_OK)
          
class NotificationsListUpdateView(APIView):
    """
    API endpoint to retrieve and update user notifications.
    HTTP POLLING is used to get notifications count every 60 seconds - default behaviour of GET.

    GET:
    - Query params:
        - read_all (bool - default False): If True, returns all notifications. If False, returns only unread notifications.
        - only_count (bool - default True): If True, returns only the count of notifications.
    - Returns a list of notifications and their count.

    POST:
    - Marks all notifications as read for the user.
    - Returns a message with the number of notifications marked as read.
    """
    def get(self, request):
        """
        Retrieve notifications for the authenticated user.

        Query parameters:
        - read_all (bool): Return all notifications if True, unread only if False.
        - only_count (bool): Return only the count if True.

        Returns:
        - count: Number of notifications
        - all_notifications: List of all notifications (if only_count is False)
        - unread_notifications: List of unread notifications (if only_count is False)
        """
        read_all = request.query_params.get('read_all', 'false').lower() in ['true', 't', '1']
        only_count = request.query_params.get('only_count', 'true').lower() in ['true', 't', ] #HTTP polling
        notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
        if not read_all:
            #default behavior
            notifications = notifications.filter(is_read=False)
        if only_count:
            return  Response({"count": notifications.count()}, status=status.HTTP_200_OK)       
        serializer = NotificationSerializer(notifications, many=True)
        unread_serializer = NotificationSerializer(notifications.filter(is_read=False), many=True)
        return Response({"count": len(serializer.data), "all_notifications":serializer.data, "unread_notifications": unread_serializer.data}, status=status.HTTP_200_OK)
    def post(self, request):
        """
        (Old method. New method is PUT in NotificationsMarkReadView)
        Mark all notifications as read for the authenticated user.
        """
        #read all
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message":f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)

class NotificationRetrieveUpdateView(APIView):
    """
    (OLD method. New method is PUT in NotificationsMarkReadView)
    API endpoint to retrieve and update a specific notification.
    """
    
    def get(self, request, id):
        """
        Retrieve a specific notification by ID for the authenticated user.
        If the notification does not exist or does not belong to the user, returns a 404 error.
        """
        
        notification = get_object_or_404(Notification, id=id, user=request.user)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        """
        Mark a specific notification as read by ID for the authenticated user.
        """
        
        notification = get_object_or_404(Notification, id=id, user=request.user)
        if notification.is_read:
            return Response({"error":"You already marked this notification as read"}, status=status.HTTP_400_BAD_REQUEST)
        notification.is_read = True
        notification.save()
        return Response({"message":f"You marked this notification as read, id: {id}"}, status=status.HTTP_200_OK)

class MySubscriptionsView(APIView):

    """
    API endpoint to retrieve the authenticated user's subscriptions.
    GET:
    - Returns a list of subscriptions for the authenticated user.
    - Each subscription includes the creator's username, profile picture, and whether the user is subscribed
    """
    
    def get(self, request):
        # print(request.path)
        # print(f"Request comes from {request.headers.get('referer')} to host: {request.headers.get('host')}")        
        subscriptions = request.user.subscriptions.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileView(APIView):
    """
    API endpoint to retrieve a user's profile by username
    Includes information about whether the authenticated user is subscribed to the profile's creator or owns this page.
    Includes posts of the creator and background image if applicable or default background image.
    GET:
    - Retrieves the profile of a user by username.
    """
    
    permission_classes = [IsAuthenticated]
    def get(self, request, username):
        profile = get_object_or_404(CustomUser, username=username)
        is_subscribed = Subscription.objects.filter(creator=profile, subscriber=request.user).exists()
        if is_subscribed and request.user.id != profile.id:
            Subscription.objects.filter(creator=profile, subscriber=request.user).update(last_visited=timezone.now())
        serializer = ProfileSerializer(profile, context={'is_subscribed': is_subscribed, 'my_page': profile.id == request.user.id, "request":request,}) 
        if profile.background_picture:
            background_image = profile.background_picture.url
        else:
            background_image = settings.PLATFORM_BACKGROUND_IMAGE    
        return Response({"profile":serializer.data, "my_page": profile.id == request.user.id, "is_subscribed": is_subscribed, "background_image": background_image}, status=status.HTTP_200_OK)

class PostReportLikeView(APIView):
    """
    API endpoint to report or like/unlike a post
    POST:
    - Reports a post if the user is not the author and has not reported it before.
    - Returns a message indicating the report status.
    PUT:
    - Likes a post if the user has not liked it before, or unlikes it if the user has already liked it.
    - Returns a message indicating the like/unlike status and the updated likes count.
    """
    
    def get_post(self, id):
        """
        Retrieve a post by ID and checks 
        whether the user posted it 
        or subscribed to the creator 
        or the post is not paid.
        """
        
        post = get_object_or_404(Post, id=id)
        if post.author == self.request.user:
            return post
        try:
            subscription = Subscription.objects.get(creator=post.author, subscriber=self.request.user)
        except Subscription.DoesNotExist:
            if not post.is_paid:
                return post
            raise PermissionDenied("You are not subscribed!")
        
        if not subscription.is_active:
            raise PermissionDenied("Your subscription is not active!")
        return post
    def post(self, request, id):

        """
        Report a post if the user is not the author and has not reported it before.
        """
        post = self.get_post(id=id)
        if post.author == request.user:
            return Response({"error": "You cannot report your own post"}, status=status.HTTP_400_BAD_REQUEST)
        if post.reports.filter(id=request.user.id).exists():
            return Response({"error": "You already reported this post"}, status=status.HTTP_400_BAD_REQUEST)
        post.reports.add(request.user)
        Notification.objects.create(
        user=post.author,
        category='other',
        message= f'somebody reported the post: "{post.title[:10]}"',
        related_post=post
        )
        return Response({"message":"You reported the post"}, status=status.HTTP_201_CREATED)
    def put(self, request, id):

        """
        Likes/unlikes a post.
        """
        
        post = self.get_post(id=id)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            print(post.likes.count())
            Notification.objects.filter(
                user=post.author,
                fromuser=request.user,
                category='like',
                related_post=post
                ).delete()
            return Response({"message":"You unliked the post", "likes_count": post.likes.count()}, status=status.HTTP_200_OK)
        else:
            post.likes.add(request.user)
            if request.user != post.author:
                Notification.objects.create(
                user=post.author,
                fromuser=request.user,
                category='like',
                message= f'{request.user.username} liked the post: "{post.title[:10]}"',
                related_post=post
                )
            return Response({"message":"You liked the post", "likes_count": post.likes.count()}, status=status.HTTP_200_OK)

class CreatorDetailView(APIView):
    """
    API endpoint to retrieve and update a creator's profile.
    GET:
    - Retrieves the creator's profile information.
    PUT:
    - Updates the creator's profile information, including the greeting message.
    """
    
    permission_classes = [IsAuthenticated, IsCreator]
    def get(self, request):

        """
        Retrieve the current user's profile information.
        """

        serializer = CreatorSerializer(request.user, context={"request":request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request):

        """
        Update the current user's profile information and greeting message.
        If the user does not have a subscription plan, it will not update the greeting message.
        """
        # print(request.data)
        new_greeting_message = request.data.get("greeting_message")
        if new_greeting_message:
            try:
                request.user.subscription_plan.greeting_message = new_greeting_message
                request.user.subscription_plan.save()
            except AttributeError:
                print("User does not have a subscription_plan.")
            except Exception as e:
                print(f"Unexpected error while updating greeting_message: {e}")    
        serializer = CreatorSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)    
class PostCreateView(APIView):
    """
    API endpoint to create a new post.
    POST:
    - Creates a new post with the provided data.
    - Requires the user to be authenticated and a creator.
    - Returns a success message upon successful creation.
    """
    
    permission_classes = [IsAuthenticated, IsCreator]
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response({"message":"You successfully created a post!"}, status=status.HTTP_201_CREATED)
class PostDetailView(APIView):
    """
    API endpoint to retrieve, update, or delete a specifit post by its ID.
    GET:
    - Retrieves a post by its ID.
    PUT:
    - Updates a post by its ID with the provided data.
    DELETE:
    - Deletes a post by its ID.
    Requires the user to be authenticated and a creator.
    Raises a PermissionDenied exception if the user is not the author of the post.
    """
    
    permission_classes = [IsAuthenticated, IsCreator]
    def get_post(self, pk):
        """
        Retrieve a post by its ID and check if the user is the author.
        """
        
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
    """
    API endpoint to become a creator with Stripe.
    POST:
    - Requires the user to be authenticated and not already a creator.
    - Accepts price and greeting_message in the request data.
    - Creates a Stripe price and a SubscriptionPlan in the database.
    - Returns a success message with the subscription ID and Stripe price ID.
    - Returns an error if the user is already a creator or if required fields are missing.
    """
    
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if SubscriptionPlan.objects.filter(creator=request.user).exists():
            return Response({"error":"You already a creator!"}, status=status.HTTP_400_BAD_REQUEST)
        price = request.data.get('price')
        greeting_message = request.data.get('greeting_message')
        print(price)
        print(greeting_message)
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
    """
    API endpoint to create a Stripe checkout session for a subscription.
    POST:
    - Requires the user to be authenticated.
    - Accepts a username in the request data to identify the creator.
    - Checks if the user is already subscribed to the creator.
    - Creates a Stripe checkout session with the creator's subscription plan.
    - Returns the checkout URL for the frontend to redirect the user to Stripe for payment.
    """
    
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
                f'api/success/',
                cancel_url=YOUR_DOMAIN + 'api/cancel/',
            )
            return Response({"checkout_url": checkout_session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Server error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)  
class SuccessView(TemplateView):
    """
    API endpoint to render a success page after a successful payment.
    """
    
    template_name = 'success.html'
class CancelView(TemplateView):
    """
    API endpoint to render a cancel page after a failed payment.
    """
    
    template_name = 'cancel.html'

class SubscriptionCancelView(APIView):
    """
    API endpoint to cancel a user's subscription.
    POST:
    - Requires the user to be authenticated.
    - Accepts a username in the request data to identify the creator.
    - Checks if the user is subscribed to the creator.
    - Cancels the Stripe subscription and removes the subscription from the database.
    """
    
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
        return Response({"message":"Subscription was cancelled!"})    
       
@csrf_exempt
def stripe_webhook(request):
    """
    Webhook endpoint to handle Stripe events.
    Handles events such as checkout session completion, subscription trial ending, and subscription cancellation.
    - Processes the event and updates the database accordingly.
    - Sends a greeting email to the subscriber upon successful subscription.
    - Sends a goodbye email to the subscriber upon subscription cancellation.
    - Creates notifications for the creator about new subscriptions and cancellations.
    - Returns a 200 status code for successful processing or 400 for errors.
    """
    
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
        print(f"Creator: {creator_username}, Subscriber: {subscriber_username}")
        creator = get_object_or_404(CustomUser, username=creator_username)
        subscriber = get_object_or_404(CustomUser, username=subscriber_username)
        subscriber_email=customer_details['email']
        new_subscription = Subscription(creator=creator, subscriber=subscriber, stripe_subscription_id=subscription_id, subscriber_stripe_email=subscriber_email)
        new_subscription.save()
        print("Subscription was created!")
        try:
            send_mail(
                subject='Greeting Message',
                message=creator.subscription_plan.greeting_message,
                from_email=os.environ.get("EMAIL_HOST_USER"),
                recipient_list=[subscriber_email]
            )
            print("Email has been sent")
        except Exception as e:
            print(f"Failed to send greeting email: {e}")
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
        subscriber_email = sub.subscriber_stripe_email
        creator_username = sub.creator.username
        sub.delete()
        print("Subscription was deleted!")
        subscriber_email = sub.subscriber_stripe_email
        # send_mail(subject='Goodbye Message',
        #         message="We are sad to hear that you are leaving! You will not be charged for this subscription anymore. \n\n\n\n Best wishes,\nPersonal Blog Support team",
        #         from_email=os.environ.get("EMAIL_HOST_USER"),
        #         recipient_list=[subscriber_email])
        send_goodbye_email(fromemail=os.environ.get("EMAIL_HOST_USER"), toemail=[subscriber_email], creator_username=creator_username)
        creator = get_object_or_404(CustomUser, username=creator_username)
        Notification.objects.create(user=creator, category='subscription', message='somebody unsubscribed from you')
        #maybe send for analytics
        return HttpResponse(status=200)
    return HttpResponse(status=200)


# Authentication below #
class RegisterView(APIView):
    """
    API endpoint to register a new user.
    """
    
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"You successfully created an account!"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class LoginLogoutView(APIView):
    """
    API endpoint to log in and log out a user.
    POST:
    - Authenticates the user with username and password.
    - Returns access and refresh tokens in cookies.
    DELETE:
    - Logs out the user by blacklisting the refresh token and deleting cookies.
    """
    
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
            "message":"You logged in!", "username": user.username, "is_creator": user.is_creator, "notifications_count": Notification.objects.filter(user=user, is_read=False).count(), "is_authenticated": True
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
                pass  #can ignore or log the error

        response = Response({"message":"You logged out!"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    
class RefreshView(APIView):
    """
    API endpoint to refresh the access token using the refresh token.
    GET:
    - Requires the user to provide a refresh token in cookies.
    - Validates the refresh token and generates a new access token.
    - Returns the new access token in a cookie.
    """
    
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
    """
    API endpoint to return the username, creator status, and authentication status of the user.
    Initial request from the frontend to check esssential user information.
    """
    
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user and request.user.is_authenticated:
            print()
            return Response({"username":request.user.username,"is_creator":request.user.is_creator, "is_authenticated":True}, status=status.HTTP_200_OK)
        else:
            return Response({"username":"", "is_creator":False, "is_authenticated":False}, status=status.HTTP_200_OK)
#            