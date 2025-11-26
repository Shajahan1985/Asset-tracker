from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views import View


class LoginView(View):
    """Handle user login requests"""
    
    def get(self, request):
        """Display login form"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})
    
    def post(self, request):
        """Process login credentials and create session"""
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
        
        return render(request, 'authentication/login.html', {'form': form})


class LogoutView(View):
    """Handle user logout requests"""
    
    def post(self, request):
        """Terminate session and clear authentication data"""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')
    
    def get(self, request):
        """Allow GET requests for logout as well"""
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')


def dashboard_view(request):
    """Simple dashboard view for authenticated users"""
    return render(request, 'authentication/dashboard.html')
