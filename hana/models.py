from django.db import models
from django.contrib.auth.models import User
import datetime
from django.utils import timezone
from django.urls import reverse
import os


# Create your models here.

def get_attachment_upload_dir(instance, filename):
    """Determine upload dir for task attachment files.
    """

    return "/".join(["tasks", "attachments", str(instance.task.id), filename])


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
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
    note = models.TextField(blank=True, null=True)
    priority = models.NullBooleanField(blank=True, null=True)
    status = models.IntegerField(choices=TASK_STATUS, default=TASK_STATUS[0][0])
    placed_date = models.DateField(auto_now=True)
    due_date = models.DateTimeField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    completed_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="hana_created_by",
        on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User,
        null=True,
        blank=True,
        related_name="hana_assigned_to",
        on_delete=models.CASCADE)

    @property
    def task_status_name(self):
        return TASK_STATUS[self.task_status][1]

    def overdue_status(self):
        "Returns whether the Tasks's due date has passed or not."
        if self.due_date and datetime.date.today() > self.due_date:
            return True

    def get_absolute_url(self):
        return reverse("task_detail", kwargs={"task_id": self.id})
        # Auto-set the Task creation / completed date

    def save(self, **kwargs):
        # If Task is being marked complete, set the completed_date
        if self.completed:
            self.completed_date = datetime.datetime.now()
            self.status = 3
        super(Task, self).save()

    def __str__(self):
        return self.name


class Info(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(default=datetime.datetime.now)
    email_from = models.CharField(max_length=320, blank=True, null=True)
    email_message_id = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True)

    class Meta:
        # an email should only appear once per task
        unique_together = ("task", "email_message_id")

    @property
    def author_text(self):
        if self.author is not None:
            return str(self.author)

        assert self.email_message_id is not None
        return str(self.email_from)


class Attachment(models.Model):
    """
    Defines a generic file attachment for use in M2M relation with Task.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    file = models.FileField(upload_to=get_attachment_upload_dir, max_length=255)

    def filename(self):
        return os.path.basename(self.file.name)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def __str__(self):
        return f"{self.task.id} - {self.file.name}"
