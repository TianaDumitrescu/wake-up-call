from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("account/", views.account, name="account"),
    path("delete-alarm/", views.delete_alarm, name="delete_alarm"),
    path("create-alarm/", views.create_alarm, name="create_alarm"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]