from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.views import View
from django.utils.encoding import force_text
from django.contrib.auth.models import User, Group
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from .tokens import account_activation_token
from django.views.generic import CreateView, DeleteView, UpdateView, ListView, DetailView
from django.contrib import messages
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from dal import autocomplete
from django.core.mail import EmailMessage
import openpyxl
from django.core.exceptions import ValidationError
from .models import *
from .forms import SignUpForm
from django.db.models import Q
import random


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.xlsx', '.xls']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


def toggle_task_completed(task_id: int) -> bool:
    """Toggle the `completed` bool on Task from True to False or vice versa."""
    try:
        task = Task.objects.get(id=task_id)
        task.completed = not task.completed
        task.save()
        return True

    except Task.DoesNotExist:
        messages.info(f"Task {task_id} not found.")
        return False

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
                    form.add_error(None, "Your account is not active")
            else:
                # user is None
                form.add_error(None, "Wrong email or password")
        return render(request, "hana/login.html", {'form': form})


class UserLogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You are now logged out")
        return redirect(reverse('home'))

class ExcelUploadView(LoginRequiredMixin, View):

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
        for row in active_sheet.iter_rows(min_row=2, max_col=2):
            row_data = list()
            for cell in row:
                row_data.append(str(cell.value))
            excel_data.append(row_data)
            Task.objects.create(name=row_data[0], due_date=row_data[1], created_by=self.request.user)
        print(excel_data)
        return redirect("excel-table")
        # return render(request, 'hana/excel_upload.html', {"excel_data": excel_data})


class UsersListView(View):
    def get(self, request):
        users = User.objects.all()
        return render(request, "hana/users_list.html", {'users': users})


class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('user-list')
    template_name = "hana/employee_confirm_delete.html"

class UserUpdateView(UpdateView):
    model = User
    success_url = reverse_lazy('user-list')
    form_class = SignUpForm
    template_name = 'hana/user_update_form.html'


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
    success_url = reverse_lazy('home')

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostCommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['title', 'content']

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)


class EmployeePostkView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_authenticated:
            posts = Post.objects.filter(author=request.user)
            return render(request, "hana/user_posts.html", {'posts': posts})
        return redirect(reverse('user-login'))


class ExcelTableView(ListView):
    model = Task
    template_name = 'hana/excel_view.html'
    context_object_name = 'tasks'
    paginate_by = 10
    ordering = ['name']


class TaskAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Task.objects.none()

        qs = Task.objects.all()

        if self.q:
            qs = qs.filter(Q(name__istartswith=self.q) |
                           Q(note__icontains=self.q))

        return qs


class TaskAddView(LoginRequiredMixin, CreateView):
    form_class = AddEditTaskForm
    template_name = "hana/task_create.html"
    success_url = reverse_lazy('excel-table')

    def form_valid(self, form):
        # form save
        form.instance.created_by = self.request.user
        self.object = form.save(commit=False)
        self.object.save()

        return super().form_valid(form)


class TaskSearchResultView(ListView):
    model = Task
    template_name = 'hana/task_list.html'
    context_object_name = "found_tasks"

    def get_queryset(self):
        query_string = self.request.GET.get("q").strip()
        if query_string:
            found_tasks = Task.objects.filter(
                Q(name__icontains=query_string) |
                Q(note__icontains=query_string)
            )
        else:
            found_tasks = Task.objects.none()
            print(found_tasks)
        return found_tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query_string'] = self.request.GET.get("q")
        return context


class TaskEditView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = AddEditTaskForm
    success_url = reverse_lazy('excel-table')


class TaskDetailView(LoginRequiredMixin, View):
    def get(self, request, task_id):
        if request.user.is_authenticated:
            user = request.user
            task = get_object_or_404(Task, pk=task_id)
            comment_list = Info.objects.filter(task=task_id).order_by('-date')
            form = AddEditTaskForm(instance=task)

            context = {
                'form': form,
                'task': task,
                'comment_list':comment_list,
                'user' :user,
            }
        return render(request, "hana/task_detail.html", context)

    def post(self, request, task_id):
        # Save task edits
        task = get_object_or_404(Task, pk=task_id)
        if request.POST.get("add_comment"):
            Info.objects.create(
                author=request.user, task=task,
                body=(request.POST["comment-body"].strip())
            )
            messages.success(request, "Comment posted")
            return redirect(reverse_lazy("task-detail", args=[task_id,]))
        request.POST.get("add_edit_task")
        form = AddEditTaskForm(request.POST, instance=task)
        if form.is_valid():
            if request.POST.get("notify"):
                current_site = get_current_site(request)
                subject = render_to_string('email/assigned_subject.txt', {"task": task})
                body = render_to_string('email/assigned_body.txt', {
                    'task': task,
                    'site': current_site,
                })
                to_email = ""
                if task.assigned_to:
                    task.status = 1
                    to_email = task.assigned_to.email
                    email = EmailMessage(subject, body, to=[to_email])
                    email.send()
                    messages.success(request, 'Notification email has been sent to employee!')
                    form.save()
                    messages.success(request, "Task sucessfully submitted!")
                else:
                    messages.warning(request, "No email defined to sent the info! Task can't be submitted!")
            else:
                form.save()
                messages.success(request, "Task sucessfully submitted without notification email!")
            return redirect(reverse('excel-table'))
        else:
            print(form.errors)
        return render(request, 'hana/task_detail.html', locals())


class TaskAllocateView(View):
    def post(self, request):
        if request.POST.get("task_allocate") is not None:
            tasks = Task.objects.filter(assigned_to=None)
            for task in tasks:
                task.assigned_to = random.choice(User.objects.all())
                task.status = 1
                task.save()
                current_site = get_current_site(request)
                subject = render_to_string('email/assigned_subject.txt', {"task": task})
                body = render_to_string('email/assigned_body.txt', {
                    'task': task,
                    'site': current_site,
                })
                to_email = task.assigned_to.email
                email = EmailMessage(subject, body, to=[to_email])
                email.send()
            if tasks:
                messages.success(request, "Tasks succesfully allocated to your employees. Check status!")
                messages.success(request, ('Notification email has been sent to assignees!'))
            else:
                messages.warning(request, "All tasks already allocated!")
                messages.warning(request, ('Notification email already sent!'))

            return redirect(reverse("excel-table"))
        return redirect(reverse("excel-table"))

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('excel-table')

class EmployeeTaskView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_authenticated:
            tasks = Task.objects.filter(assigned_to=request.user)
            return render(request, "hana/employee_task.html", {'tasks': tasks})
        return redirect(reverse('user-login'))


class ToggleDoneUndoneView(LoginRequiredMixin, View):
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        results_changed = toggle_task_completed(task.id)
        if results_changed:
            if not task.completed:
                task.completed_date = datetime.datetime.now()
            messages.success(request, f"Changed completion status for task: {task.name}")
            return redirect("task-detail", task_id=task_id)

class AddAttachementView(View):
    def get(self, request):
        form = ModelFormWithFileField()
        return render(request, "hana/task_detail.html", {"form": form})

    def post(self, request):
        form = ModelFormWithFileField(request.POST, request.FILES)
        if form.is_valid():
            form.instance.added_by = self.request.user
            form.instance.task = self.request.task
            self.object = form.save(commit=False)
            self.object.save()
            messages.info(request, "Attachement {} succesfully uploaded".format(self.object.filename))
            return redirect(reverse('task-update'))
        else:
            return render(request, "hana/task_detail.html", {"form": form})


class RemoveAttachementView(DeleteView):
    model = Attachment
    success_url = reverse_lazy('task-update')


class TaskCommentAddView(LoginRequiredMixin, CreateView):
    form_class = AddInfoForm
    template_name = "hana/task_detail.html"
    success_url = reverse_lazy('excel-table')

    def get(self, request, *args, **kwargs):
        if request.POST.get("add_comment"):
            self.object = None
            return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # form save
        form.instance.created_by = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        return super().form_valid(form)
'''
class InfoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Info
    fields = ['body', ]
    context_object_name = 'task'
    success_url = reverse_lazy('task-detail', kwargs =[task,])

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        info = self.get_object()
        if self.request.user == info.author:
            return True
        return False

'''
class InfoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Info
    template_name = "hana/info_confirm_delete.html"

    def test_func(self):
        info = self.get_object()
        if self.request.user == info.author:
            return True
        return False

    def get_success_url(self):
        return reverse('task-detail', args=(self.object.task.id,))

class TaskStatusFilterView(View):
    def get(self, request):
        form = TaskStatusFilterForm()
        return render(request, "hana/excel_view.html", {"form" : form})

    def post(self, request):
        form = TaskStatusFilterForm(request.POST)
        if form.is_valid():
            status = Task.objects.filter(
                status=form.cleaned_data['status']
            )
        return render(request, "hana/excel_view.html", locals())
