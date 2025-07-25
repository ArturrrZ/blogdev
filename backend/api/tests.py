from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import CustomUser, Post, Subscription, SubscriptionPlan, Notification
from django.shortcuts import get_object_or_404
import json
import os
import time
# Create your tests here.

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.testuser_data = {
            "username":"testuser",
            "email":"testemail@gmail.com",
            "password":"testpassword"
        }
        #get creator cookies for next tests👇
        creator_obj = CustomUser.objects.create_user(username="creator", password="creator", email="creator@gmail.com", is_creator=True)
        SubscriptionPlan.objects.create(creator=creator_obj, price=1000, stripe_price_id='fake_stripe_id', greeting_message='Welcome')
        creator_login_response = self.client.post("/api/accounts/login_logout/", {
            "username": "creator",
            "password":"creator"
        })
        
        self.creator_cookies = creator_login_response.cookies #access token will be still available
        self.client.delete("/api/accounts/login_logout/") #refresh token will be in token_blacklist
        #get another creator cookies for next tests👇
        CustomUser.objects.create_user(username="another_creator", password="another_creator", email="another_creator@gmail.com", is_creator=True)
        another_creator_login_response = self.client.post("/api/accounts/login_logout/", {
            "username": "another_creator",
            "password":"another_creator"
        })
        
        self.another_creator_cookies = another_creator_login_response.cookies #access token will be still available
        self.client.delete("/api/accounts/login_logout/") #refresh token will be in token_blacklist
        #get user(not a creator) cookies for next tests 👇
        CustomUser.objects.create_user(username="user", password="user", email="user@gmail.com", is_creator=False)
        user_login_response = self.client.post("/api/accounts/login_logout/",{
            "username": "user",
            "password":"user"
        })
        
        self.user_cookies = user_login_response.cookies
        self.client.delete("/api/accounts/login_logout/") #refresh token will be in token_blacklist

    def create_testpost(self, creator=None, title=None, body=None, is_paid=None):
        if creator is None:
            creator="creator"
        if title is None:
            title="test post"
        if body is None:
            body="test body"        
        if is_paid is None:
            is_paid=False
        creator = CustomUser.objects.get(username=creator)
        return Post.objects.create(author=creator, title=title, body=body, is_paid=is_paid)    
    def subscribe(self, creator=None, subscriber=None, stripe_subscription_id=None):
        if creator is None:
            creator="creator"
        if subscriber is None:
            subscriber="user"
        if stripe_subscription_id is None:
            stripe_subscription_id = 'sub_fake_1'    
        creator_obj = CustomUser.objects.get(username=creator)        
        subscriber_obj = CustomUser.objects.get(username=subscriber)        
        return Subscription.objects.create(creator=creator_obj, subscriber=subscriber_obj, stripe_subscription_id=stripe_subscription_id)
    
    def test_user_is_creator(self):
        creator = CustomUser.objects.get(username="creator")
        self.assertEqual(creator.is_creator, True)      
      
    def test_registration_successful(self):
        response = self.client.post('/api/accounts/register/', {
            "username":"testuser",
            "email":"testemail@gmail.com",
            "password":"testpassword"
        })    
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "You successfully created an account!")
    def test_registration_wrong_method(self):
        response = self.client.get("/api/accounts/register/")    
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    def test_registration_bad_request(self):
        response = self.client.post("/api/accounts/register/", {
            "username":"usernamewithoutPasswordAndEmail"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 
    def test_registartion_user_already_exist(self):
        first_response = self.client.post("/api/accounts/register/", self.testuser_data) 
        response = self.client.post("/api/accounts/register/", self.testuser_data)  
        # print(response.data)
        self.assertIn('error', response.data) 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_successful(self):
        self.client.post('/api/accounts/register/', self.testuser_data)
        response = self.client.post('/api/accounts/login_logout/', 
        {"username": self.testuser_data["username"], "password": self.testuser_data["password"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], 'You logged in!')
        self.assertIn('access_token', response.cookies)   
        self.assertIn('refresh_token', response.cookies)
    def test_login_missing_fields(self):
        response = self.client.post('/api/accounts/login_logout/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data['error'], 'username and password are required fields!')
    def test_logout_successful(self):
        self.client.post("/api/accounts/register/", self.testuser_data)
        login_response = self.client.post("/api/accounts/login_logout/", {
            "username": self.testuser_data['username'],
            "password":self.testuser_data["password"]
        })
        self.client.cookies = login_response.cookies
        logout_response = self.client.delete("/api/accounts/login_logout/")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.data["message"], "You logged out!")
        self.assertEqual(logout_response.cookies["access_token"].value, "")
        self.assertEqual(logout_response.cookies["refresh_token"].value, "")
    #added creator user to initial db
    def test_refresh_token_successful(self):
        self.client.post("/api/accounts/register/", self.testuser_data)
        login_response = self.client.post("/api/accounts/login_logout/", {
            "username": self.testuser_data['username'],
            "password":self.testuser_data["password"]
        })
        self.client.cookies = login_response.cookies
        response = self.client.get('/api/accounts/refresh_token/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)   
    def test_refresh_token_missing_cookie(self):
        response = self.client.get('/api/accounts/refresh_token/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)    
    def test_refresh_token_invalid_cookie(self):
        self.client.cookies['refresh_token'] = 'invalid.token.value'
        response = self.client.get('/api/accounts/refresh_token/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data['error'], 'Invalid refresh token')
    def test_me_view(self):
        not_authenticated_response = self.client.get("/api/accounts/me/")
        self.assertEqual(not_authenticated_response.status_code, status.HTTP_200_OK)     
        self.assertEqual(not_authenticated_response.data['is_creator'], False)     
        self.assertEqual(not_authenticated_response.data['is_authenticated'], False)     
        self.assertEqual(not_authenticated_response.data['username'], "") 

        self.client.cookies = self.creator_cookies #authenticate
        authenticated_response = self.client.get("/api/accounts/me/")
        self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)     
        self.assertEqual(authenticated_response.data['is_creator'], True)     
        self.assertEqual(authenticated_response.data['is_authenticated'], True)     
        self.assertEqual(authenticated_response.data['username'], "creator") 
    def test_creator_get(self):
        self.client.cookies = self.creator_cookies
        response = self.client.get("/api/creator/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("about", response.data)
        # print(response.data)
    def test_creator_edit(self):
        self.client.cookies = self.creator_cookies
        response = self.client.put("/api/creator/", {
            "about": "My New desription!",
            "first_name":"New First Name"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        get_response = self.client.get("/api/creator/")
        self.assertEqual("My New desription!", get_response.data["about"])
        self.assertEqual("New First Name", get_response.data["first_name"])
        # print(get_response.data)    
    def test_creator_error(self):
        self.client.cookies = self.user_cookies #log in as user
        not_creator_response = self.client.get("/api/creator/")
        self.assertEqual(not_creator_response.status_code, status.HTTP_403_FORBIDDEN)
        not_creator_response = self.client.put("/api/creator/", {
            "about":"New About me!"
        })
        self.assertEqual(not_creator_response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_creator_post_CRUD(self):
        self.client.cookies = self.creator_cookies
        #create
        response = self.client.post("/api/creator/posts/",{
            "title": "New post",
            "body": "Some body"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #retrieve
        retrieve_response = self.client.get("/api/creator/posts/1/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['title'], 'New post')
        self.assertEqual(retrieve_response.data['body'], 'Some body')
        self.assertIsNone(retrieve_response.data['image'])
        self.assertTrue(retrieve_response.data['is_my'])
        self.assertFalse(retrieve_response.data['is_paid'])
        #update
        update_reponse = self.client.put("/api/creator/posts/1/",{
            "is_paid": True,
            "title":"New Title"
        })
        self.assertEqual(update_reponse.status_code, status.HTTP_200_OK)

        retrieve_after_update_response = self.client.get("/api/creator/posts/1/")
        self.assertEqual(retrieve_after_update_response.data['title'], 'New Title')
        self.assertTrue(retrieve_after_update_response.data['is_paid'])

        #delete
        delete_response = self.client.delete("/api/creator/posts/1/")
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)

        deleted_response = self.client.get("/api/creator/posts/1/")
        self.assertEqual(deleted_response.status_code, status.HTTP_404_NOT_FOUND)
    def test_creator_post_forbidden_user(self):
        self.client.cookies = self.user_cookies
        create_response = self.client.post("/api/creator/posts/", {
            "title": "I am not a creator",
            "body":"And I can not create a post :("
        })
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
    def test_creator_post_forbidden_another_user(self):
        self.client.cookies = self.creator_cookies
        self.client.post("/api/creator/posts/", {"title":"New Post", "body":"New Body"})
        #log in as another creator
        self.client.cookies = self.another_creator_cookies

        retrieve_response = self.client.get("/api/creator/posts/1/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(retrieve_response.data['detail'], 'This is not your post!')

        update_response = self.client.put("/api/creator/posts/1/", {"title":"New Title from another creator"})
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

        delete_response = self.client.delete("/api/creator/posts/1/")
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
    def test_creator_post_empty(self):
        self.client.cookies = self.creator_cookies
        response = self.client.post("/api/creator/posts/", {"title":"", "body":""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    def test_creator_post_404(self):
        self.client.cookies = self.creator_cookies
        response = self.client.get("/api/creator/posts/31/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)    
    
    def test_post_report(self):
        testpost = self.create_testpost(creator="creator")
        reports = testpost.reports.count() #should be 0
        subscription = self.subscribe(creator="creator", subscriber="user")
        self.client.cookies = self.user_cookies

        response = self.client.post(f"/api/posts/report_like/{testpost.id}/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'You reported the post')
        reported = testpost.reports.count()
        self.assertEqual(reported, reports + 1)

        duplicate_response = self.client.post(f"/api/posts/report_like/{testpost.id}/")
        unduplicated_reports = testpost.reports.count()
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(duplicate_response.data['error'], 'You already reported this post')
        self.assertEqual(reported, unduplicated_reports)    
    def test_post_report_not_sub(self):
        post = self.create_testpost(is_paid=True)
        self.client.cookies = self.user_cookies

        response = self.client.post(f"/api/posts/report_like/{post.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You are not subscribed!')
    def test_post_report_own_post(self):
        self.client.cookies = self.creator_cookies
        post = self.create_testpost()
        
        response = self.client.post(f"/api/posts/report_like/{post.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'You cannot report your own post')
    
    def test_post_like(self):
        testpost = self.create_testpost()
        likes = testpost.likes.count()
        self.subscribe()
        self.client.cookies = self.user_cookies

        response = self.client.put(f"/api/posts/report_like/{testpost.id}/")
        liked = testpost.likes.count()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'You liked the post')
        self.assertEqual(liked, likes + 1)


        unlike_response = self.client.put(f"/api/posts/report_like/{testpost.id}/")
        unliked = testpost.likes.count()
        self.assertEqual(unlike_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unlike_response.data['message'], 'You unliked the post')
        self.assertEqual(unliked, liked - 1)
    def test_post_like_not_sub(self):
        testpost = self.create_testpost(is_paid=True)
        likes = testpost.likes.count()
        self.client.cookies = self.user_cookies

        response = self.client.put(f"/api/posts/report_like/{testpost.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 
        self.assertEqual(testpost.likes.count(), likes)
    def test_post_like_own_post(self):
        testpost = self.create_testpost()
        self.client.cookies = self.creator_cookies

        response = self.client.put(f"/api/posts/report_like/{testpost.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'You liked the post')

        unlike_response = self.client.put(f"/api/posts/report_like/{testpost.id}/")
        self.assertEqual(unlike_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unlike_response.data['message'], 'You unliked the post')
    
    def test_profile_creator_sub(self):
        self.client.cookies = self.user_cookies
        self.subscribe()
        self.create_testpost()

        response = self.client.get("/api/profile/creator/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['username'], 'creator')
        self.assertTrue(response.data['profile']['is_creator'])
        self.assertEqual(response.data['profile']['posts_total'], 1)
        self.assertEqual(response.data['profile']['subscribers'], 1)
        self.assertTrue(response.data['is_subscribed']) 
        self.assertFalse(response.data['my_page'])
    def test_profile_creator_not_sub(self):
        self.client.cookies = self.user_cookies

        self.create_testpost()

        response = self.client.get("/api/profile/creator/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['username'], 'creator')
        self.assertTrue(response.data['profile']['is_creator'])
        self.assertEqual(response.data['profile']['posts_total'], 1)
        self.assertEqual(response.data['profile']['subscribers'], 0)
        self.assertFalse(response.data['is_subscribed']) 
        self.assertFalse(response.data['my_page'])    
    def test_profile_creator_own(self):
        self.client.cookies = self.creator_cookies

        response = self.client.get("/api/profile/creator/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['username'], 'creator')
        self.assertTrue(response.data['profile']['is_creator'])
        self.assertFalse(response.data['is_subscribed']) 
        self.assertTrue(response.data['my_page'])    
    def test_profile_user(self):
        self.client.cookies = self.creator_cookies
        
        response = self.client.get('/api/profile/user/')
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['is_creator'], False)
        self.assertEqual(response.data['profile']['username'], 'user')
        self.assertEqual(response.data['my_page'], False)
        self.assertEqual(response.data['is_subscribed'], False)
    def test_profile_user_own(self):
        self.client.cookies = self.user_cookies
        
        response = self.client.get('/api/profile/user/')
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['is_creator'], False)
        self.assertEqual(response.data['profile']['username'], 'user')
        self.assertEqual(response.data['my_page'], True)
        self.assertEqual(response.data['is_subscribed'], False)    
    def test_profile_not_auth(self):
        response = self.client.get("/api/profile/creator/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    def test_locked_post_content_hidden_for_not_subscriber(self):
        self.client.cookies = self.user_cookies
        post = self.create_testpost()
        post.is_paid = True
        post.image = 'asd'
        post.save()

        response = self.client.get("/api/profile/creator/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['posts_paid'], 1)
        locked_post = response.data['profile']['posts'][0]
        self.assertEqual(locked_post['title'], "Locked Content")
        self.assertEqual(locked_post['image'], '/static/api/locked_content.jpg')
        self.assertIsNone(locked_post['body'])
    def test_my_subscriptions(self):
        self.client.cookies = self.user_cookies
        self.subscribe()
        response = self.client.get('/api/my_subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        subscription = response.data[0]
        self.assertEqual(subscription['creator']['username'], 'creator')
        self.assertEqual(subscription['is_active'], True)
        self.assertIn('new_posts', subscription)
        # +1 new post
        self.assertEqual(subscription['new_posts'], 0)
        self.client.get("/api/profile/creator/")
        time.sleep(1)
        self.create_testpost()
        time.sleep(1)
        response = self.client.get('/api/my_subscriptions/')
        subscription = response.data[0]
        # print(response.data)
        self.assertEqual(subscription['new_posts'], 1)
        #mark as read
        self.client.get("/api/profile/creator/")
        response = self.client.get('/api/my_subscriptions/')
        subscription = response.data[0]
        # print(response.data)
        self.assertEqual(subscription['new_posts'], 0)


    def test_my_subscriptions_not_auth(self):
        response = self.client.get("/api/my_subscriptions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #stripe
    def test_creator_become_unsuccessful(self):
        creator = get_object_or_404(CustomUser, username='another_creator')
        sub_plan = SubscriptionPlan.objects.create(
            creator = creator,
            price = 1000,#in cents
            stripe_price_id = 'unique-product-id',
            greeting_message = 'Hello, my new sub!',
        )
        self.client.cookies = self.another_creator_cookies

        response = self.client.post('/api/creator/become/', {'price': 10, 'greeting_message': 'Hello my new sub!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'You already a creator!')

        sub_plan.delete()

        response = self.client.post('/api/creator/become/', {
            'price': 10,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Both Price and Greeting message fields are required!')

        response = self.client.post('/api/creator/become/', {
            'price': '10$',
            'greeting_message': 'Hello my new sub!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Price must be a number')
    
    @patch("api.views.stripe.Price.create")  
    def test_successful_creation(self, mock_stripe_create):
        self.client.cookies = self.another_creator_cookies
        mock_stripe_create.return_value = type("obj", (object,), {"id": "fake_stripe_id2"})
        data = {"price": 10, "greeting_message": "Thanks for subscribing!"}
        response = self.client.post("/api/creator/become/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("subscription_id", response.data)
        self.assertTrue(SubscriptionPlan.objects.filter(creator=get_object_or_404(CustomUser, username='creator')).exists())

    def test_checkout_session_unsuccessful(self):
        subscription = self.subscribe()
        self.client.cookies = self.user_cookies

        response = self.client.post('/api/subscribe/', {'username':'creator'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'You already subscribed')

        subscription.delete()
        response = self.client.post('/api/subscribe/', {'username':'another_creator'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No subscription plan for this user')
    
    @patch("api.views.stripe.checkout.Session.create")
    def test_checkout_session(self, mock_stripe_checkout):
        self.client.cookies = self.user_cookies
        mock_stripe_checkout.return_value = type("obj", (object,), {"url": "checkout_url.com"})
        response = self.client.post('/api/subscribe/', {'username':'creator'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['checkout_url'], 'checkout_url.com')
    
    def test_subscription_cancel_unsuccessful(self):
        self.client.cookies = self.user_cookies
        response = self.client.post('/api/cancel_subscription/', {'username':'creator'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No such subscription')

    @patch("api.views.stripe.Subscription.cancel") 
    def test_subscription_cancel(self, mock_stripe_cancel):
        self.subscribe() #sub_fake_1
        self.client.cookies = self.user_cookies
        response = self.client.post('/api/cancel_subscription/', {'username':'creator'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Subscription was cancelled!')
        mock_stripe_cancel.assert_called_once_with("sub_fake_1")
    
    @patch("api.views.stripe.Webhook.construct_event")
    @patch("api.views.send_goodbye_email")
    def test_stripe_webhook_subscription_deleted(self, mock_send_mail ,mock_construct_event):
        sub = self.subscribe() #sub_fake_1
        event_payload = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_fake_1",
                    "metadata": {"creator":"creator", "subscriber":"user"}
                }
            }
        }

        mock_construct_event.return_value = event_payload
        #make sure that sub exists before deleting
        self.assertTrue(Subscription.objects.filter(stripe_subscription_id="sub_fake_1").exists()) 

        response = self.client.post(
            "/api/webhooks/stripe/",
            data=json.dumps(event_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake"
        )
        mock_send_mail.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.filter(stripe_subscription_id="sub_fake_1").exists())

        self.client.cookies = self.creator_cookies
        response = self.client.get("/api/notifications/all/?only_count=false")
        self.assertEqual(response.data['unread_notifications'][0]['category'], 'subscription')
        self.assertEqual(response.data['unread_notifications'][0]['message'], 'somebody unsubscribed from you')

    @patch("api.views.stripe.Webhook.construct_event")    
    @patch("api.views.send_mail")
    def test_stripe_webhook_checkout_session_completed(self,mock_send_mail, mock_construct_event):
        creator=get_object_or_404(CustomUser, username='creator')
        subscriber=get_object_or_404(CustomUser, username='user')
        
        event_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "subscription": "sub_fake_1",
                    "metadata": {"creator":"creator", "subscriber":"user"},
                    'customer_details': {'email':'customeremail'}
                }
            }
        }

        mock_construct_event.return_value = event_payload
        response = self.client.post(
            "/api/webhooks/stripe/",
            data=json.dumps(event_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake"
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_mail.assert_called_once_with(
            subject='Greeting Message',
            message=creator.subscription_plan.greeting_message,
            from_email=os.environ.get("EMAIL_HOST_USER"),
            recipient_list=['customeremail']
)
        self.assertTrue(Subscription.objects.filter(creator=creator, subscriber=subscriber, stripe_subscription_id='sub_fake_1').exists())
        self.assertTrue(Notification.objects.filter(user=creator,fromuser=subscriber, category='subscription').exists())
    
    def test_notifications_all(self):
        creator = get_object_or_404(CustomUser, username='creator')
        user = get_object_or_404(CustomUser, username='user')
        notification = Notification.objects.create(user=creator, category='other', message='some message from admin')
        time.sleep(1)
        self.client.cookies = self.creator_cookies
        #first check
        response = self.client.get("/api/notifications/all/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        self.client.cookies = self.user_cookies
        post = self.create_testpost()
        self.subscribe()
        self.client.put(f'/api/posts/report_like/{post.id}/')
        
        #second check
        self.client.cookies=self.creator_cookies
        response = self.client.get("/api/notifications/all/?only_count=false&read_all=true")
        # print(response.data)
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        # print(response.data)
        self.assertEqual(response.data['unread_notifications'][0]['category'], 'like')
        self.assertEqual(response.data['unread_notifications'][0]['fromuser']['username'], 'user')
        self.assertEqual(response.data['unread_notifications'][1]['category'], 'other')
        self.client.cookies = self.user_cookies
        self.client.put(f'/api/posts/report_like/{post.id}/') #unlike
        
        #third check
        self.client.cookies=self.creator_cookies
        response = self.client.get("/api/notifications/all/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        self.client.cookies = self.user_cookies
        self.client.post("/api/notifications/all/") #read all another user
        #4th check
        self.client.cookies=self.creator_cookies
        response = self.client.get("/api/notifications/all/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        self.client.post("/api/notifications/all/") #read all
        #5th check
        self.client.cookies=self.creator_cookies
        response = self.client.get("/api/notifications/all/")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        #6th check
        self.client.cookies=self.creator_cookies
        response = self.client.get("/api/notifications/all/?read_all=t")
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    def test_notification_details(self):
        creator = get_object_or_404(CustomUser, username='creator')
        user = get_object_or_404(CustomUser, username='user')
        notification = Notification.objects.create(user=creator, category='other', message='some message from admin')
        self.client.cookies = self.creator_cookies
        #first check
        response = self.client.get(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notifications = Notification.objects.filter(user=creator)
        self.assertEqual(notifications.filter(is_read=False).count(), 1)

        response = self.client.patch(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'You marked this notification as read, id: 1')
        self.assertEqual(notifications.filter(is_read=False).count(), 0)

        response = self.client.patch(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'You already marked this notification as read')
    def test_notification_details_wrong_user(self):
        creator = get_object_or_404(CustomUser, username='creator')
        user = get_object_or_404(CustomUser, username='user')
        notification = Notification.objects.create(user=creator, category='other', message='some message from admin')
        self.client.cookies = self.user_cookies
        #first check
        response = self.client.get(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


        response = self.client.patch(f"/api/notifications/{notification.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Notification.objects.filter(is_read=False, user=creator).count(), 1)
    def test_notification_mark_read(self):
        creator = get_object_or_404(CustomUser, username='creator')
        notification = Notification.objects.create(user=creator, category='other', message='some message from admin')
        notification_id = notification.id
        self.client.cookies = self.creator_cookies

        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 1)
        #mark read
        response = self.client.put("/api/notifications/mark-read/", {"ids": [notification_id]}, content_type="application/json")
        print(response.data)
        self.assertEqual(response.data['message'], 'marked as read')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        time.sleep(1)
        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 0)
        #mark unread
        unread_response = self.client.put("/api/notifications/mark-read/", {"ids": [notification_id], "mark_read": False,}, content_type="application/json")
        self.assertEqual(unread_response.data['message'], 'marked as unread')
        self.assertEqual(unread_response.status_code, status.HTTP_200_OK)
        
        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 1)
    def test_notification_mark_read_all(self):
        creator = get_object_or_404(CustomUser, username='creator')
        Notification.objects.create(user=creator, category='other', message='some message from admin')
        self.client.cookies = self.creator_cookies

        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 1)

        response = self.client.put("/api/notifications/mark-read/", {"mark_all": True}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 0)
    def test_notification_mark_read_error(self):
        creator = get_object_or_404(CustomUser, username='creator')
        Notification.objects.create(user=creator, category='other', message='some message from admin')
        self.client.cookies = self.creator_cookies

        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 1)

        response = self.client.put("/api/notifications/mark-read/", {"ids": [1]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'ids field have to be a list')

        response = self.client.put("/api/notifications/mark-read/", {"ids": ["hello", True, False]}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No notification IDs provided.')

        response = self.client.put("/api/notifications/mark-read/", content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No notification IDs provided.')

        response = self.client.put("/api/notifications/mark-read/", {"mark_all":"true"},content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'mark_read and mark_all fields have to be booleans')

        response = self.client.put("/api/notifications/mark-read/", {"mark_read":"true"},content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'mark_read and mark_all fields have to be booleans')
    def test_notification_report(self):
        post = self.create_testpost()
        self.client.cookies = self.user_cookies
        self.client.post(f"/api/posts/report_like/{post.id}/")

        self.client.cookies = self.creator_cookies
        response = self.client.get("/api/notifications/all/?only_count=false")
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['unread_notifications'][0]['message'], f'somebody reported the post: "{post.title}"')
    def test_notification_like_own_post(self):
        post = self.create_testpost()
        self.client.cookies = self.creator_cookies
        response = self.client.put(f"/api/posts/report_like/{post.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 0)
        #unlike 
        response = self.client.put(f"/api/posts/report_like/{post.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/notifications/all/")
        self.assertEqual(response.data['count'], 0)
        
    #       