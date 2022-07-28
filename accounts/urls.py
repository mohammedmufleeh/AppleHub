from django.urls import path
from . import views




urlpatterns = [
    path('login',views.signin,name='login'),
    path('register',views.signup,name='register'),
    path('logout',views.signout,name='logout'),
    path('activate/<uidb64>/<token>/',views.activate, name='activate')
]