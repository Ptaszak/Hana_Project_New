"""first_application URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, reverse_lazy
from hana import views as ex_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from hana.tokens import account_activation_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ex_views.PostListView.as_view(), name="home"),
    path('user/<str:username>', ex_views.UserPostsListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', ex_views.PostDetailView.as_view(), name='post-detail'),
    path('post/new/', ex_views.PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', ex_views.PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', ex_views.PostDeleteView.as_view(), name='post-delete'),
    path('post/<int:pk>/comment/', ex_views.CommentCreateView.as_view(), name='add-comment'),
    path('signup/', ex_views.SignupView.as_view(), name="signup"),
    path('profile/', ex_views.UserView.as_view(), name='profile'),
    # path('sent/', ex_views.ActivationSentView.as_view(), name="activation_sent"),
    path('activate/<slug:uidb64>/<slug:token>/', ex_views.ActivateView.as_view(), name='activate'),
    path('user_login/', ex_views.UserLoginView.as_view(), name='user-login'),
    path('user_logout/', ex_views.UserLogoutView.as_view(), name='user-logout'),
    # path('user_create/', ex_views.UserCreateView.as_view(), name='user-create'),
    # path('signup/', ex_views.SignUpView.as_view(), name="signup"),
    path('reset-password/done', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_done_reset.html'),
        name='reset_password_done'),
    path(
        'reset-password/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset.html',
            html_email_template_name='registration/reset_password_email.html',
            success_url=reverse_lazy('reset_password_done'),
            token_generator=account_activation_token),
        name='reset_password'
    ),
    path(
        'reset-password-confirmation/<str:uidb64>/<str:token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/reset_password_update.html',
            post_reset_login=False,
            post_reset_login_backend='django.contrib.auth.backends.ModelBackend',
            success_url=reverse_lazy('reset_password_complete'),
            token_generator=account_activation_token),
        name='password_reset_confirm'
    ),
    path('reset-password/complete', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_complete_reset.html'),
        name='reset_password_complete'),
    path('excel_upload', ex_views.ExcelUploadView.as_view(), name='excel-upload'),
    path('user_list', ex_views.UsersListView.as_view(), name = "user-list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
