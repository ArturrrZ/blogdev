from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    # custom fields
    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(max_length=20, unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_creator = models.BooleanField(default=False)
    profile_picture = models.ImageField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    background_picture = models.ImageField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)   
    youtube = models.URLField(null=True, blank=True)   
    # Add related_name to avoid clashes
    groups = models.ManyToManyField(Group, related_name='user_groups')
    user_permissions = models.ManyToManyField(Permission, related_name='user_permissions')
    
    def __str__(self):
        return self.username