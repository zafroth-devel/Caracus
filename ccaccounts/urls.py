from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.contrib.auth.views import(
    LoginView,
    LogoutView)

from ccaccounts.forms import AuthenticationForm as authform
from .views import (
    PasswordChangeView,
    PasswordChangeDoneView,
    HinyangoCreateUserView,
    HinyangoCreateUserDoneView,
    HinyangoResetUserView,
    HinyangoResetUserDoneView,
    DeleteUserStep1View,
    DeleteUserStep2View,
    ModifyUserDetailsView,
    HinyangoAccountRedirect)

# APP --> ACCOUNTS

urlpatterns = [
    #url(r'^login/$',LoginView.as_view(template_name='ccloginv3.html',authentication_form=authform),name='login'),
    url(r'^login/$',LoginView.as_view(template_name='hinyango_user_login.html',authentication_form=authform),name='login'),
    url(r'^logout/$',LogoutView.as_view(next_page=reverse_lazy('home')),name='logout'),
    url(r'^change/password/$',PasswordChangeView.as_view(),name='cpview'),
    url(r'^password/changed/$',PasswordChangeDoneView.as_view(),name='password_change_done'),
    url(r'^create/user/$',HinyangoCreateUserView.as_view(),name='add_hinyango_user'),
    url(r'^user/created/$',HinyangoCreateUserDoneView.as_view(),name='add_hinyango_user_done'),
    url(r'^reset/password/$',HinyangoResetUserView.as_view(),name='reset_password'),
    url(r'^password/reset/$',HinyangoResetUserDoneView.as_view(),name='reset_password_done'),
    url(r'^delete/user/$',DeleteUserStep1View.as_view(),name='delete_user'),
    url(r'^delete/user/(?P<uname>[a-zA-Z0-9]+)$',DeleteUserStep2View.as_view(),name='final_remove_user'),
    url(r'^modify/user/$',ModifyUserDetailsView.as_view(),name='modify_existing_user'),
    url(r'^login/redirect/$',HinyangoAccountRedirect.as_view(),name='login_redirect')
]
