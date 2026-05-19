from django.contrib import admin
from django.urls import path,include
from .views import *
urlpatterns = [
   path('register/', RegisterView.as_view(), name='register'),
   path('login/', LoginView.as_view(), name='login'),
   path('profile/', UserDetailsAPIView.as_view(), name='user-details'),
   path('profile/personal/', UserpersonalDetailsAPIView.as_view(), name='user-personal-details'),

]
