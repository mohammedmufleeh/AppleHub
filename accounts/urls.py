from unicodedata import name
from django.urls import path
from . import views




urlpatterns = [
    path('login',views.signin,name='login'),
    path('register',views.signup,name='register'),
    path('logout',views.signout,name='logout'),
    path('user_dashboard',views.user_dashboard,name='user_dashboard'),
    path('my_orders',views.my_orders,name='my_orders'),
    path('cancel_order/<int:order_number>/', views.cancel_order, name='cancel_order'),
     path('view_order/<int:order_number>/', views.view_order, name='view_order'),

    path('activate/<uidb64>/<token>/',views.activate, name='activate'),
    path('forgotPassword', views.forgotPassword,  name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/',views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword', views.resetPassword,  name='resetPassword')

] 