from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg',upload_to= 'profile_pics')
    email = models.EmailField(max_length=150)
    signup_confirmation = models.BooleanField(default=False)


    def __str__(self):
        return f'{self.user.username} Profile'


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

class Comment(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.post.id})

TASK_STATUS = (
    (0, "not assigned"),
    (1, "assigned"),
    (2, "in progres"),
    (3, "done"),
    (4, "cancelled")

)
class Task(models.Model):
    name = models.CharField(max_length=248)
    quantity = models.IntegerField()
    norm = models.IntegerField()
    priority = models.NullBooleanField(blank=True, null=True)
    status = models.IntegerField(choices=TASK_STATUS, default=TASK_STATUS[0][0])
    placed_date = models.DateField(auto_now=True)

    def __str__(self):
        return self.name
