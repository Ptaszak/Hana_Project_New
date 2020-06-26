from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.views import View
from django.utils.encoding import force_text
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from .forms import SignUpForm
from .tokens import account_activation_token
from django.views.generic import CreateView, DeleteView, UpdateView, FormView, ListView, DetailView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import *
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMessage
import openpyxl
from openpyxl.styles import Font, Fill
from django.core.exceptions import ValidationError
import os
from .models import *
from pyexcel_xls import get_data as xls_get
from pyexcel_xlsx import get_data as xlsx_get
from django.utils.datastructures import MultiValueDictKeyError
from .forms import SignUpForm
import six

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.xlsx', '.xls']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


class HomeView(View):
    def get(self, request):
        return render(request, 'base1.html')


class UserView(LoginRequiredMixin, View):
    def get(self, request):
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        ctx = {
            "u_form": u_form,
            "p_form": p_form
        }
        return render(request, "hana/profile.html", ctx)

    def post(self, request):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "{}, your account has been updated!".format(request.user))
            return redirect('profile')
        else:
            u_form = UserUpdateForm(request.POST, instance=request.user)
            p_form = ProfileUpdateForm(request.POST, request.Files, instance=request.user.profile)
            ctx = {
                "u_form": u_form,
                "p_form": p_form
            }
            return render(request, "hana/profile.html", ctx)


'''class ActivationSentView(View):
    def get(self, request):
        return render(request, 'hana/activation_sent.html')'''


class ActivateView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            # checking if the user exists, if the token is valid.
        if user is not None and account_activation_token.check_token(user, token):
            # if valid set active true
            user.is_active = True
            # set signup_confirmation true
            user.profile.signup_confirmation = True
            user.save()
            login(request, user)
            messages.success(request, ('Your account have been confirmed.'))
            return redirect('home')
        else:
            messages.warning(request, ('The confirmation link was invalid, possibly because it has already been used.'))
            return redirect('home')


class SignupView(View):
    form_class = SignUpForm
    template_name = 'hana/signup.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            group = Group.objects.get(name="Employee")
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is confirmed
            user.save()
            group.user_set.add(user)

            current_site = get_current_site(request)
            subject = 'Activate Your hana-Account'
            message = render_to_string('hana/activation_request.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(subject, message, to=[to_email])
            email.send()
            messages.success(request, ('Authentication email has been sent to employee to complete registration.'))
            return redirect('home')

        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    def get(self, request):
        form = UserLoginForm()
        return render(request, "hana/login.html", {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST or None)
        if form.is_valid():  # uruchomienie walidacji
            user = form.authenticate_user()
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.GET.get('next'):
                        return redirect(request.GET.get('next'))

                    return redirect(reverse('home'))
                else:
                    form.add_error(None, "Konto nie jest aktywne")
            else:
                # user is None
                form.add_error(None, "Nieprawidłowy login lub hasło")
        return render(request, "hana/login.html", {'form': form})


class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You are now logged out")
        return redirect(reverse('home'))


'''
class UserCreateView(CreateView):
    form_class = UserCreateForm
    template_name = "hana/user_create.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
'''
'''
class SignUpView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, "hana/signup.html", {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST or None)
        if form.is_valid():  # uruchomienie walidacji
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
        else:
            return render(request, "hana/signup.html", {'form': form})
'''


class PasswordResetView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = PasswordResetForm()
        return render(request, "hana/login.html", {"form": form})

    def post(self, request, pk):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, pk=pk)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.info(request, "Hasło dla użytkownika {} zostało zmienione".format(user.username))
            login(request, user)
            return redirect('index')
        return render(request, "exercises/user_login.html", {"form": form})


class ExcelUploadView(View):
    def get(self, request):
        return render(request, "hana/excel_upload.html")

    def post(self, request):
        excel_file = request.FILES['excel_file']
        #  validations here to check extension or file size
        validate_file_extension(excel_file)
        wb = openpyxl.load_workbook(excel_file)
        # getting a particular sheet by name out of many sheets
        active_sheet = wb.active
        print(active_sheet)

        excel_data = list()
        print(excel_data)

        # iterating over the rows and
        # getting value from each cell in row
        for row in active_sheet.iter_rows(min_row=2, max_col=6):
            row_data = list()
            for cell in row:
                row_data.append(str(cell.value))
            excel_data.append(row_data)
            Task.objects.create(name=row_data[0], quantity=row_data[1],
                                norm=row_data[2], priority=row_data[3],
                                status=row_data[4], placed_date=row_data[5] )
        return render(request, 'hana/excel_upload.html', {"excel_data": excel_data})

class UsersListView(View):
    def get(self, request):
        users = User.objects.all()
        return render(request, "hana/users_list.html", {'users': users})


class PostListView(ListView):
    model = Post
    template_name = 'hana/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostsListView(ListView):
    model = Post
    template_name = 'hana/user_posts.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post
    template_name = 'hana/post_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(PostCreateView, self).form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['title', 'content']

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)
'''
class ParseExcel(View):
    def post(self, request, format=None):
        try:
            excel_file = request.FILES['files']
        except MultiValueDictKeyError:
            return redirect('home')

        if (str(excel_file).split('.')[-1] == "xls"):
            data = xls_get(excel_file, column_limit=7)
        elif (str(excel_file).split('.')[-1] == "xlsx"):
            data = xlsx_get(excel_file, column_limit=7)
        else:
            return redirect("home")

        tasks = data["Task"]

        if len(tasks > 1):  # we have task data
            for task in tasks:
                if (len(task) > 0):  # the row is not blank
                    if (task[0] != "NO"):  # is not a header
                        if (len(task) < 7):
                            i = len(task)
                            while (i < 7):
                                task.append("")
                                i += 1

        c = Task.objects.filter(name=task[1])

        if (c.count() == 0):
            Task.objects.create(
                name = task[1],
                quantity = task[2],
                norm = task[3],
                priority = task[4],
                status = task[5],
                placed_date = task[6]
            )

            return render(request, 'hana/excel_sheet_upload.html', {"excel_file": excel_file})

'''

class ExcelTableView(ListView):
    model = Task
    template_name = 'hana/excel_view.html'
    context_object_name = 'tasks'
    paginate_by = 10

class ExcelTableAddView(CreateView):
    model = Task
    fields = "__all__"
    success_url = reverse_lazy('excel-table')


