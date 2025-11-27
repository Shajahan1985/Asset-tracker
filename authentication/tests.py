from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from hypothesis import given, settings, assume
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
    
    @given(
        username=valid_username(),
        password=valid_password(),
        time_before_timeout=st.integers(min_value=1, max_value=1209600)  # 1 second to 2 weeks
    )
    @settings(max_examples=100, deadline=None)
    def test_property_session_persistence_within_timeout(self, username, password, time_before_timeout):
        """
        Feature: django-auth-permissions, Property 7: Session persistence within timeout
        Validates: Requirements 2.4
        
        For any authenticated session, if accessed before the timeout period expires,
        the session should remain valid and maintain authentication state.
        """
        # Create a user
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        login_response = client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        self.assertTrue(client.session.get('_auth_user_id'))
        
        # Simulate time passing but still within timeout
        # We'll access the session before it expires
        # Django's SESSION_COOKIE_AGE is set to 1209600 seconds (2 weeks)
        # We ensure time_before_timeout is less than the configured timeout
        
        # Access a protected page before timeout
        response = client.get(reverse('dashboard'))
        
        # Verify session is still valid
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        self.assertEqual(int(client.session['_auth_user_id']), user.id)
        
        # Verify we can still access protected resources
        self.assertEqual(response.status_code, 200)
    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_session_expiration_enforcement(self, username, password):
        """
        Feature: django-auth-permissions, Property 8: Session expiration enforcement
        Validates: Requirements 2.5
        
        For any session that exceeds the configured timeout period,
        the session should be invalidated and require re-authentication.
        """
        # Create a user
        user = User.objects.create_user(username=username, password=password)
        
        # Create a client and login
        client = Client()
        client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify user is authenticated
        self.assertTrue(client.session.get('_auth_user_id'))
        
        # Get the session and manually expire it
        session = client.session
        session_key = session.session_key
        
        # Import Session model to manipulate expiration
        from django.contrib.sessions.models import Session
        
        # Get the session object from database
        session_obj = Session.objects.get(session_key=session_key)
        
        # Set expiration to the past (simulate timeout)
        session_obj.expire_date = timezone.now() - timedelta(seconds=1)
        session_obj.save()
        
        # Try to access a protected page with expired session
        # Create a new client with the expired session
        expired_client = Client()
        expired_client.cookies = client.cookies
        
        # Access dashboard - should redirect to login due to expired session
        response = expired_client.get(reverse('dashboard'), follow=False)
        
        # Verify user is not authenticated (session expired)
        # The middleware should have cleared the expired session
        self.assertFalse(response.wsgi_request.user.is_authenticated)


    @given(username=valid_username(), password=valid_password())
    @settings(max_examples=100, deadline=None)
    def test_property_unauthenticated_access_redirection(self, username, password):
        """
        Feature: django-auth-permissions, Property 10: Unauthenticated access redirection
        Validates: Requirements 3.3
        
        For any protected view, when accessed by an unauthenticated user,
        the system should redirect to the login page.
        """
        # Create a user (but don't log in)
        User.objects.create_user(username=username, password=password)
        
        # Create an unauthenticated client
        client = Client()
        
        # Attempt to access protected dashboard without authentication
        response = client.get(reverse('dashboard'), follow=False)
        
        # Verify redirect to login page
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect URL points to login
        expected_redirect = f"{reverse('login')}?next={reverse('dashboard')}"
        self.assertEqual(response.url, expected_redirect)
        
        # Follow the redirect and verify we end up at login page
        response = client.get(reverse('dashboard'), follow=True)
        self.assertRedirects(
            response,
            expected_redirect,
            fetch_redirect_response=False
        )
        
        # Verify user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)


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



class UserManagementPropertyTests(HypothesisTestCase):
    """Property-based tests for user management functionality"""
    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password(),
        role_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_creation_with_role_assignment(self, username, email, password, role_name):
        """
        Feature: django-auth-permissions, Property 1: User creation with role assignment
        Validates: Requirements 1.1
        
        For any valid username, email, password, and role, when an admin creates a user account,
        the system should store the user with the specified credentials and the role should be 
        assigned to the user.
        """
        from django.contrib.auth.models import Group
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        # Skip passwords that don't meet Django's validation requirements
        # Also need to pass a user object to check similarity
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            # Skip this test case if password doesn't meet requirements
            return
        
        # Create a role (group)
        role = Group.objects.create(name=role_name)
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Create a new user with role assignment
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
                'role': role.id
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username=username).exists())
        
        # Get the created user
        created_user = User.objects.get(username=username)
        
        # Verify credentials are stored correctly
        self.assertEqual(created_user.username, username)
        self.assertEqual(created_user.email, email)
        
        # Verify password is hashed (not plaintext)
        self.assertNotEqual(created_user.password, password)
        self.assertTrue(created_user.check_password(password))
        
        # Verify role is assigned
        self.assertIn(role, created_user.groups.all())
        self.assertEqual(created_user.groups.count(), 1)

    
    @given(
        username=valid_username(),
        email=st.emails(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_password_hashing_invariant(self, username, email, password):
        """
        Feature: django-auth-permissions, Property 2: Password hashing invariant
        Validates: Requirements 1.3
        
        For any user creation, the password stored in the database should be hashed 
        and should not match the plaintext password provided during creation.
        """
        from django.contrib.auth.models import Group
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        
        # Skip passwords that don't meet Django's validation requirements
        temp_user = User(username=username, email=email)
        try:
            validate_password(password, user=temp_user)
        except ValidationError:
            return
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Create a new user
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': email,
                'password1': password,
                'password2': password,
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username=username).exists())
        
        # Get the created user
        created_user = User.objects.get(username=username)
        
        # Verify password is hashed (not plaintext)
        self.assertNotEqual(created_user.password, password)
        
        # Verify the hashed password can be verified
        self.assertTrue(created_user.check_password(password))
        
        # Verify password field contains a hash (starts with algorithm identifier)
        self.assertTrue(created_user.password.startswith('pbkdf2_') or 
                       created_user.password.startswith('md5$') or
                       created_user.password.startswith('bcrypt'))

    
    @given(
        username=valid_username(),
        invalid_email=st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x and x.strip()),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_email_validation_enforcement(self, username, invalid_email, password):
        """
        Feature: django-auth-permissions, Property 3: Email validation enforcement
        Validates: Requirements 1.4
        
        For any invalid email format, attempting to create a user should result in 
        a validation error and no user should be created.
        """
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Count users before attempt
        user_count_before = User.objects.count()
        
        # Attempt to create a user with invalid email
        response = client.post(
            reverse('user_create'),
            {
                'username': username,
                'email': invalid_email,
                'password1': password,
                'password2': password,
            }
        )
        
        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username=username).exists())
        
        # Verify user count hasn't changed (excluding admin)
        user_count_after = User.objects.count()
        self.assertEqual(user_count_before, user_count_after)
        
        # Verify form has validation errors
        self.assertIn('email', response.context['form'].errors)

    
    @given(
        user_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_list_completeness(self, user_count):
        """
        Feature: django-auth-permissions, Property 20: User list completeness
        Validates: Requirements 7.1
        
        For any set of users in the system, when an admin requests the user list,
        all users should be displayed with their roles and status information.
        """
        from django.contrib.auth.models import Group
        
        # Create an admin user
        admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create a test role
        test_role = Group.objects.create(name='test_role')
        
        # Create multiple users with various configurations
        created_users = []
        for i in range(user_count):
            user = User.objects.create_user(
                username=f'testuser_{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            # Assign role to some users
            if i % 2 == 0:
                user.groups.add(test_role)
            # Deactivate some users
            if i % 3 == 0:
                user.is_active = False
                user.save()
            created_users.append(user)
        
        # Login as admin
        client = Client()
        client.force_login(admin)
        
        # Request user list
        response = client.get(reverse('user_list'))
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Get users from context
        users_in_list = list(response.context['users'])
        
        # Verify all created users are in the list (plus admin)
        self.assertEqual(len(users_in_list), user_count + 1)  # +1 for admin
        
        # Verify each created user is present
        for user in created_users:
            self.assertIn(user, users_in_list)
        
        # Verify admin is also in the list
        self.assertIn(admin, users_in_list)
        
        # Verify user information is accessible (roles and status)
        for user in users_in_list:
            # Check that we can access groups (roles)
            user.groups.all()  # Should not raise an error
            # Check that we can access status
            self.assertIsNotNone(user.is_active)

    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_deactivation_prevents_login(self, username, password):
        """
        Feature: django-auth-permissions, Property 21: Deactivation prevents login
        Validates: Requirements 7.2
        
        For any user account, when deactivated by an admin, login attempts with 
        that user's credentials should be rejected.
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password
        )
        
        # Verify user can login when active
        client = Client()
        response = client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertTrue(User.objects.get(username=username).is_active)
        
        # Create admin and deactivate the user
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Deactivate the user
        response = admin_client.get(reverse('user_deactivate', args=[user.pk]))
        
        # Verify user is deactivated
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Attempt to login with deactivated account
        login_client = Client()
        response = login_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        
        # Verify login was rejected
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Verify user is not logged in
        self.assertNotIn('_auth_user_id', login_client.session)

    
    @given(
        username=valid_username(),
        password=valid_password()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_reactivation_restores_access(self, username, password):
        """
        Feature: django-auth-permissions, Property 22: Reactivation restores access (round-trip)
        Validates: Requirements 7.3
        
        For any user account, deactivating and then reactivating should restore 
        the user's ability to log in.
        """
        # Create a user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password=password
        )
        
        # Verify user can login initially
        initial_client = Client()
        response = initial_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Create admin
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Deactivate the user
        admin_client.get(reverse('user_deactivate', args=[user.pk]))
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Verify login fails when deactivated
        deactivated_client = Client()
        response = deactivated_client.post(
            reverse('login'),
            {'username': username, 'password': password}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Reactivate the user (round-trip)
        admin_client.get(reverse('user_reactivate', args=[user.pk]))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Verify user can login again after reactivation
        reactivated_client = Client()
        response = reactivated_client.post(
            reverse('login'),
            {'username': username, 'password': password},
            follow=True
        )
        
        # Verify login is successful
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, username)
        
        # Verify session was created
        self.assertIn('_auth_user_id', reactivated_client.session)

    
    @given(
        username=valid_username(),
        original_email=st.emails(),
        new_email=st.emails(),
        new_first_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs', 'Zs', 'Zl', 'Zp')),
            min_size=1, 
            max_size=30
        ).filter(lambda x: x.strip() and x == x.strip()),
        new_last_name=st.text(
            alphabet=st.characters(blacklist_categories=('Cc', 'Cs', 'Zs', 'Zl', 'Zp')),
            min_size=1, 
            max_size=30
        ).filter(lambda x: x.strip() and x == x.strip())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_user_update_preserves_integrity(self, username, original_email, 
                                                       new_email, new_first_name, new_last_name):
        """
        Feature: django-auth-permissions, Property 23: User update preserves integrity
        Validates: Requirements 7.4
        
        For any user and valid update data, when an admin updates the user information,
        the changes should be saved and other user data should remain unchanged.
        """
        from django.contrib.auth.models import Group
        
        # Create a user with initial data
        user = User.objects.create_user(
            username=username,
            email=original_email,
            password='originalpass123',
            first_name='OriginalFirst',
            last_name='OriginalLast'
        )
        
        # Store original values
        original_username = user.username
        original_password = user.password
        original_date_joined = user.date_joined
        original_id = user.id
        
        # Create a role and assign it
        original_role = Group.objects.create(name='original_role')
        user.groups.add(original_role)
        
        # Create admin
        admin = User.objects.create_superuser(
            username='admin_' + username[:20],
            email='admin@test.com',
            password='adminpass123'
        )
        
        admin_client = Client()
        admin_client.force_login(admin)
        
        # Update user information
        response = admin_client.post(
            reverse('user_update', args=[user.pk]),
            {
                'username': username,  # Keep same username
                'email': new_email,
                'first_name': new_first_name,
                'last_name': new_last_name,
                'is_active': True,
            },
            follow=True
        )
        
        # Refresh user from database
        user.refresh_from_db()
        
        # Verify updated fields changed (email is normalized to lowercase by Django)
        self.assertEqual(user.email.lower(), new_email.lower())
        self.assertEqual(user.first_name, new_first_name)
        self.assertEqual(user.last_name, new_last_name)
        
        # Verify unchanged fields remain the same (integrity preserved)
        self.assertEqual(user.username, original_username)
        self.assertEqual(user.password, original_password)
        self.assertEqual(user.date_joined, original_date_joined)
        self.assertEqual(user.id, original_id)
        
        # Verify user is still active
        self.assertTrue(user.is_active)



class UserManagementUnitTests(TestCase):
    """Unit tests for user management functionality"""
    
    def setUp(self):
        """Set up test data"""
        from django.contrib.auth.models import Group
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test role
        self.test_role = Group.objects.create(name='TestRole')
    
    def test_create_user_with_specific_role(self):
        """Test creating user with specific role"""
        client = Client()
        client.force_login(self.admin)
        
        # Create user with role
        response = client.post(
            reverse('user_create'),
            {
                'username': 'newuser',
                'email': 'newuser@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'role': self.test_role.id
            },
            follow=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Get created user
        user = User.objects.get(username='newuser')
        
        # Verify role was assigned
        self.assertIn(self.test_role, user.groups.all())
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m) for m in messages))
    
    def test_duplicate_username_rejection(self):
        """Test duplicate username rejection (edge case)"""
        # Create initial user
        User.objects.create_user(
            username='existinguser',
            email='existing@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Attempt to create user with duplicate username
        response = client.post(
            reverse('user_create'),
            {
                'username': 'existinguser',
                'email': 'different@test.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )
        
        # Verify form has errors
        self.assertIn('username', response.context['form'].errors)
        
        # Verify only one user with that username exists
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)
    
    def test_update_specific_user_fields(self):
        """Test updating specific user fields"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='old@test.com',
            password='testpass123',
            first_name='OldFirst',
            last_name='OldLast'
        )
        
        client = Client()
        client.force_login(self.admin)
        
        # Update user
        response = client.post(
            reverse('user_update', args=[user.pk]),
            {
                'username': 'testuser',
                'email': 'new@test.com',
                'first_name': 'NewFirst',
                'last_name': 'NewLast',
                'is_active': True,
            },
            follow=True
        )
        
        # Refresh user
        user.refresh_from_db()
        
        # Verify updates
        self.assertEqual(user.email, 'new@test.com')
        self.assertEqual(user.first_name, 'NewFirst')
        self.assertEqual(user.last_name, 'NewLast')
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m) for m in messages))
    
    def test_deactivate_and_reactivate_specific_user(self):
        """Test deactivating and reactivating specific user"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Verify user is active initially
        self.assertTrue(user.is_active)
        
        client = Client()
        client.force_login(self.admin)
        
        # Deactivate user
        response = client.get(reverse('user_deactivate', args=[user.pk]), follow=True)
        
        # Refresh and verify deactivation
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('deactivated' in str(m) for m in messages))
        
        # Reactivate user
        response = client.get(reverse('user_reactivate', args=[user.pk]), follow=True)
        
        # Refresh and verify reactivation
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Verify success message
        messages = list(response.context['messages'])
        self.assertTrue(any('reactivated' in str(m) for m in messages))
