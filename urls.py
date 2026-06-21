from django.contrib import admin
from django.urls import path
from knowledge_base import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',                  views.dashboard,      name='dashboard'),
    path('articles/',         views.article_list,   name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('labs/',             views.lab_list,        name='lab_list'),
]
