from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import CustomUser
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
        CustomUser.objects.create_user(username="creator", password="creator", email="creator@gmail.com", is_creator=True)
        creator_login_response = self.client.post("/api/accounts/login_logout/", {
            "username": "creator",
            "password":"creator"
        })
        
        self.creator_cookies = creator_login_response.cookies #access token will be still available
        self.client.delete("/api/accounts/login_logout/") #refresh token will be in token_blacklist
        #get user(not a creator) cookies for next tests 👇
        CustomUser.objects.create_user(username="user", password="user", email="user@gmail.com", is_creator=False)
        user_login_response = self.client.post("/api/accounts/login_logout/",{
            "username": "user",
            "password":"user"
        })
        
        self.user_cookies = user_login_response.cookies
        self.client.delete("/api/accounts/login_logout/") #refresh token will be in token_blacklist

        

    ##
    def test_user_is_creator(self):
        creator = CustomUser.objects.get(username="creator")
        self.assertEqual(creator.is_creator, True)      
    ##  
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
    #
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
    #
    def test_me_view(self):
        not_authenticated_response = self.client.get("/api/accounts/me/")
        self.assertEqual(not_authenticated_response.status_code, status.HTTP_200_OK)     
        self.assertEqual(not_authenticated_response.data['is_creator'], False)     
        self.assertEqual(not_authenticated_response.data['authenticated'], False)     
        self.assertEqual(not_authenticated_response.data['username'], "") 

        self.client.cookies = self.creator_cookies #authenticate
        authenticated_response = self.client.get("/api/accounts/me/")
        self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)     
        self.assertEqual(authenticated_response.data['is_creator'], True)     
        self.assertEqual(authenticated_response.data['authenticated'], True)     
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
    #       