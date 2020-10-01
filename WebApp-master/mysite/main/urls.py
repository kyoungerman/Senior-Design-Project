"""mysite URL Configuration

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

# TL;DR: this file is where we assign a view (page) to a URL.
# Basically, the path '' is website.com/ and it loads Home page.
# The path 'search' is website.com/search, and it loads the SearchResultsView page.
from django.urls import path

from . import views

urlpatterns = [
    path('', views.Home.as_view(), name='index'),
    path('search', views.SearchResultsView.as_view(), name='search_results'),
    path('historical', views.Historical, name='historical')
]
