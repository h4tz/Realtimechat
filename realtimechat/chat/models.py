from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
from datetime import timedelta

def default_expiry():
    return timezone.now() + timedelta(days=1)

class Message(models.Model):
    room = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default= default_expiry )
    
    def __str__(self):
        return f'{self.user.username} : {self.content}'


class PrivateMessage(models.Model):
    read = models.BooleanField(default=False)
    user1 = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    

class FileMessage(models.Model):
    file = models.FileField(upload_to='chat_files/')
    

class MutedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    muted_until = models.DateTimeField()
    
class ChatActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)