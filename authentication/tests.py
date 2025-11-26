from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase


# Helper strategies for generating test data
def valid_username():
    """Generate valid usernames for testing"""
    return st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48, max_codepoint=122),
        min_size=3,
        max_size=30
    ).filter(lambda x: x.strip() and x.isalnum())


def valid_password():
    """Generate valid passwords for testing"""
    return st.text(
        alphabet=st.characters(
            blacklist_characters='\x00',
            blacklist_categories=('Cs',)  # Exclude surrogates
        ),
        min_size=8,
        max_size=128
    ).filter(lambda x: '\x00' not in x)


class AuthenticationPropertyTests(HypothesisTestCase):
    """Property-based tests for authentication functionality"""
    
    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_valid_login_creates_session(self, username, password):
        """
        Feature: django-auth-permissions, Property 5: Valid login creates session
        Validates: Requirements 2.1
        
        For any user with valid credentials, successful login should create 
        an authenticated session and the user should be redirected to the dashboard.
        """
        # Create a user with the generated credentials
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client to simulate requests
        client = Client()
        
        # Attempt to login with valid credentials
        response = client.post(
            reverse('login'),
            {'username': username, 'password': password},
            follow=True
        )
        
        # Verify session was created (user is authenticated)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        
        # Verify redirect to dashboard occurred
        self.assertRedirects(response, reverse('dashboard'))
        
        # Verify session data exists
        self.assertIn('_auth_user_id', client.session)
        self.assertEqual(int(client.session['_auth_user_id']), user.id)
    
    @given(
        username=valid_username(),
        correct_password=valid_password(),
        wrong_password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_credentials_rejection(self, username, correct_password, wrong_password):
        """
        Feature: django-auth-permissions, Property 6: Invalid credentials rejection
        Validates: Requirements 2.2
        
        For any invalid credential combination (wrong username or wrong password), 
        login attempts should be rejected with an error message.
        """
        # Skip if passwords happen to be the same
        if correct_password == wrong_password:
            return
        
        # Create a user with correct credentials
        User.objects.create_user(username=username, password=correct_password)
        
        # Create a client to simulate requests
        client = Client()
        
        # Test 1: Wrong password
        response = client.post(
            reverse('login'),
            {'username': username, 'password': wrong_password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Verify error message is displayed
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
        
        # Test 2: Wrong username (non-existent user)
        response = client.post(
            reverse('login'),
            {'username': username + '_wrong', 'password': correct_password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Verify error message is displayed
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
    
    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_logout_terminates_session(self, username, password):
        """
        Feature: django-auth-permissions, Property 9: Logout terminates session
        Validates: Requirements 3.1
        
        For any authenticated user, performing logout should terminate 
        the session and clear all authentication data.
        """
        # Create a user
        User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        response = client.get(reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Store session key before logout
        session_key_before = client.session.session_key
        
        # Perform logout
        response = client.post(reverse('logout'), follow=True)
        
        # Verify user is no longer authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify session data is cleared (no auth user id)
        self.assertNotIn('_auth_user_id', client.session)
        
        # Verify redirect to login page
        self.assertRedirects(response, reverse('login'))


class AuthenticationUnitTests(TestCase):
    """Unit tests for authentication views"""
    
    def test_login_with_valid_credentials(self):
        """Test login with specific valid credentials"""
        # Create a test user
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Attempt login
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'testpass123'},
            follow=True
        )
        
        # Verify successful login
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'testuser')
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_login_with_invalid_credentials(self):
        """Test login with specific invalid credentials"""
        # Create a test user
        User.objects.create_user(username='testuser', password='correctpass')
        
        # Attempt login with wrong password
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'wrongpass'}
        )
        
        # Verify login failed
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify error message is present
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Invalid' in str(m) for m in messages))
        
        # Attempt login with non-existent username
        response = client.post(
            reverse('login'),
            {'username': 'nonexistent', 'password': 'somepass'}
        )
        
        # Verify login failed
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout_clears_session_data(self):
        """Test logout clears session data"""
        # Create and login a user
        User.objects.create_user(username='testuser', password='testpass123')
        client = Client()
        client.post(
            reverse('login'),
            {'username': 'testuser', 'password': 'testpass123'}
        )
        
        # Verify user is authenticated
        response = client.get(reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Logout
        response = client.post(reverse('logout'), follow=True)
        
        # Verify user is no longer authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify session auth data is cleared
        self.assertNotIn('_auth_user_id', client.session)
        
        # Verify redirect to login page
        self.assertRedirects(response, reverse('login'))
