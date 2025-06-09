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
    
class Post(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=50)
    body = models.TextField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    # video = models.FileField(upload_to='videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    likes = models.ManyToManyField(CustomUser, related_name='liked_posts', blank=True, null=True)
    reports = models.ManyToManyField(CustomUser, related_name='reported_posts',blank=True, null=True)
    def __str__(self):
        return f"{self.title} by {self.author.username}"   

class Subscription(models.Model):   
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscribers')
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator', 'subscriber'], name='unique_subscription')
        ]
    def clean(self):
        # Ensure a user cannot subscribe to themselves
        if self.creator == self.subscriber:
            raise ValidationError("A user cannot subscribe to themselves.")
  
    def save(self, *args, **kwargs):
        # Call clean method before saving
        self.clean()
        super().save(*args, **kwargs) 
    def __str__(self):
        return f"{self.creator} + 1: ({self.subscriber})"   

#class Subscription Plan(models.Model)
#
