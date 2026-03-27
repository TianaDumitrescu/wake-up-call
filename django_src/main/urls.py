from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("account/", views.account, name="account"),
    path("delete-alarm/", views.delete_alarm, name="delete_alarm"),
]