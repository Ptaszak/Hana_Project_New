from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout
from .models import Profile, Comment, Task, Attachment, Info, TASK_STATUS
from dal import autocomplete

class UserLoginForm(forms.Form):
    email = forms.CharField(label = 'Email')
    password = forms.CharField(label = 'Hasło', widget = forms.PasswordInput)

    def clean(self):
        user = self.authenticate_via_email()
        if not user:
            raise forms.ValidationError("Sorry, that login was invalid. Please try again.")
        else:
            self.user = user
        return self.cleaned_data

    def authenticate_user(self):
        return authenticate(
            username=self.user.username,
            password=self.cleaned_data['password'])

    def authenticate_via_email(self):
        """
            Authenticate user using email.
            Returns user object if authenticated else None
        """
        email = self.cleaned_data['email']
        if email:
            try:
                user = User.objects.get(email__iexact=email)
                if user.check_password(self.cleaned_data['password']):
                    return user
            except ObjectDoesNotExist:
                pass
        return None
'''
class UserCreateForm(UserCreationForm):
    email = forms.EmailField(label=_("Email address"),required=True,
        help_text=_("Required."))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check to see if any users already exist with this email as a username.
        try:
            match = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Unable to find a user, this is fine
            return email

        # A user was found with this as a username, raise an error.
        raise forms.ValidationError('This email address is already in use.')
    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
'''
class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Mandatory')
    last_name = forms.CharField(max_length=30, required=True, help_text='Mandatory')
    email = forms.EmailField(max_length=254, help_text='Enter a valid email address')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2', )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check to see if any users already exist with this email as a username.
        try:
            match = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Unable to find a user, this is fine
            return email
        # A user was found with this as a username, raise an error.
        raise forms.ValidationError('This email address is already in use.')

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(max_length=200)

    class Meta:
        model = User
        fields = ('username', 'email')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields =['image']

class PasswordResetForm(forms.Form):
    password = forms.CharField(label = "Hasło", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Powtórz hasło", widget=forms.PasswordInput)

    def clean(self):
        super().clean()
        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']

        if password != password2:
            raise forms.ValidationError(
                    'Podane hasła są różne'
                )


class AddEditTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        exclude = ["created_by"]
        widgets = {
            "due_date": forms.DateInput(attrs={'type':'date'}),
            "completed_date": forms.DateInput(attrs={'type': 'date'}),
            "name":forms.TextInput(),
            "note": forms.Textarea(),
        }

class AddEditTaskForm2(forms.ModelForm):
    class Meta:
        model = Task
        exclude = ["created_by", "assigned_to"]
        widgets = {
            "due_date": forms.DateInput(attrs={'type':'date'}),
            "completed_date": forms.DateInput(attrs={'type': 'date'}),
            "name":forms.TextInput(),
            "note": forms.Textarea(),
        }


class SearchForm(forms.Form):
    """Search."""
    q = forms.CharField(widget=forms.widgets.TextInput(attrs={"size": 35}))

class ModelFormWithFileField(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']

class AddInfoForm(forms.ModelForm):
    model = Info
    fields =["body",]


class TaskStatusFilterForm(forms.Form):
    a = forms.ChoiceField(label="Filter by status:", choices=TASK_STATUS)
