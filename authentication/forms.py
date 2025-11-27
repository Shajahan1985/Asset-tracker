from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class UserCreateForm(UserCreationForm):
    """Form for creating new users with role assignment"""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        help_text='Select a role to assign to this user.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise ValidationError('Enter a valid email address.')
        return email
    
    def save(self, commit=True):
        """Save user and assign role if provided"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Assign role if provided
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
        
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users"""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        help_text='Select a role to assign to this user.'
    )
    is_active = forms.BooleanField(
        required=False,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial role if user has one
        if self.instance and self.instance.pk:
            user_groups = self.instance.groups.all()
            if user_groups.exists():
                self.fields['role'].initial = user_groups.first()
            self.fields['is_active'].initial = self.instance.is_active
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise ValidationError('Enter a valid email address.')
        return email
    
    def save(self, commit=True):
        """Save user and update role"""
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Update role - clear existing and add new if provided
            user.groups.clear()
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
        
        return user
