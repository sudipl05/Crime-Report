# users/models.py

import os
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


def report_photo_upload_path(instance, filename):
    return f'photos/user_{instance.user.id}/report_{instance.id or "new"}/{filename}'

def report_video_upload_path(instance, filename):
    return f'videos/user_{instance.user.id}/report_{instance.id or "new"}/{filename}'


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    photos = models.ImageField(upload_to='images/', blank=True, null=True)
    location = models.CharField(max_length=255)  # ✅ Add this field
    videos = models.FileField(upload_to='videos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"
