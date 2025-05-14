from django import forms
from django.core.exceptions import ValidationError  # Import ValidationError
from django.contrib.auth.models import User
from .models import Report

# RegisterForm
class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    #password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password1 = forms.CharField(
    label='Password',
    widget=forms.PasswordInput,
    min_length=8,
    help_text='Minimum 8 characters.'
)

    #password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
    label='Confirm Password',
    widget=forms.PasswordInput,
    min_length=8,
    help_text='Enter the same password as above for verification.'

)
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

# ReportForm
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'description', 'location', 'photos', 'videos']  # Include location field

    photos = forms.FileField(widget=forms.FileInput(), required=False)
    videos = forms.FileField(widget=forms.FileInput(), required=False)

    # Optional: You could also add file size validation if needed, for example:
    def clean_photos(self):
        photo = self.cleaned_data.get('photos')
        if photo and photo.size > 5 * 1024 * 1024:  # 5MB size limit
            raise ValidationError("Photo file size should not exceed 5MB.")
        return photo

    def clean_videos(self):
        video = self.cleaned_data.get('videos')
        if video and video.size > 50 * 1024 * 1024:  # 50MB size limit
            raise ValidationError("Video file size should not exceed 50MB.")
        return video
