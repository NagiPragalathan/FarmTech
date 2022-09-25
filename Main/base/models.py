from email import message
from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime
from django.utils import timezone

# Create your models here.

User = get_user_model()

# meet
class RoomMember(models.Model):
    name = models.CharField(max_length=200)
    uid = models.CharField(max_length=1000)
    room_name = models.CharField(max_length=200)
    insession = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# login & profiles
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    profileimg = models.ImageField(upload_to='static/Profile/profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    image = models.ImageField(upload_to='post_images')
    caption = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    no_of_likes = models.IntegerField(default=0)

    def __str__(self):
        return self.user

class LikePost(models.Model):
    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.username

class FollowersCount(models.Model):
    follower = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    def __str__(self):
        return self.user

#Aleart
class Emergency(models.Model):
    user_id = models.IntegerField()
    number = models.CharField(max_length=100)
    messages = models.CharField(max_length=100,default="i am in trubble please help me")
    def __str__(self):
        return self.user
    
class FilesUpload(models.Model):
    user_id = models.FileField()
    Catagery = models.CharField(max_length=100)
    Topic = models.CharField(max_length=100)
    def __str__(self):
        return self.user
# this is db is used for all donar list 😁
class DonateNow(models.Model):
    dname = models.CharField(max_length=122)
    email = models.CharField(max_length=122)
    FoodT = models.CharField(max_length=122)
    FoodQ = models.CharField(max_length=122)
    address = models.CharField(max_length=122)
    phone = models.IntegerField()
    date = models.DateField(default=timezone.now)

    
    class Meta:
        verbose_name_plural = 'DonateNows' 

    def __str__(self):
        return self.email

class Volunteer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    nid = models.IntegerField()
    vemail = models.CharField(primary_key=True, max_length=122)
    password = models.CharField(max_length=122)
    vaddress = models.CharField(max_length=122)
    city = models.CharField(max_length=30)
    zip = models.CharField(max_length=50)
    describe = models.TextField()
    date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Vlunteers'

    def __str__(self):
        return self.vemail


