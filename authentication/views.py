from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import UserCreateForm, UserUpdateForm


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


@login_required
def dashboard_view(request):
    """Simple dashboard view for authenticated users"""
    return render(request, 'authentication/dashboard.html')



class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Display list of all users (admin only)"""
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    
    def get_queryset(self):
        """Return all users with their groups prefetched"""
        return User.objects.all().prefetch_related('groups').order_by('username')


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new user with role assignment (admin only)"""
    model = User
    form_class = UserCreateForm
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.add_user'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'User "{self.object.username}" created successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update existing user (admin only)"""
    model = User
    form_class = UserUpdateForm
    template_name = 'authentication/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'auth.change_user'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(self.request, f'User "{self.object.username}" updated successfully.')
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_deactivate(request, pk):
    """Deactivate a user account"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    messages.success(request, f'User "{user.username}" has been deactivated.')
    return redirect('user_list')


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_reactivate(request, pk):
    """Reactivate a user account"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f'User "{user.username}" has been reactivated.')
    return redirect('user_list')
