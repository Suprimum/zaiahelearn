"""
URL configuration for zaiahelearn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django import views
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from zaiahelearn.apps.courses import views
from django.conf.urls.static import static
from django.conf import settings

from zaiahelearn.apps.courses.views import RoleLoginView, StudentSignupView, account_delete

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='home'),
    path('courses/', include('zaiahelearn.apps.courses.urls', namespace='courses')),
    path('accounts/signup/', StudentSignupView.as_view(), name='account_signup'),
    path('accounts/login/', RoleLoginView.as_view(), name='account_login'),
    path('accounts/delete/', account_delete, name='account_delete'),
    path('accounts/', include('allauth.urls')),
    path("contact/", views.contact_us, name="contact"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)