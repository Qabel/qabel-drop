"""qabel_drop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from drop_service.views import DropView

urlpatterns = [
    url('', include('django_prometheus.urls')),

    # This is pretty much a catch-all pattern
    # Note: We could already introduce the length limit here, but it would change the API: instead of 400 for
    # invalid, too short drop IDs we'd return 404.
    url(r'^(?P<drop_id>[-_A-Za-z0-9]+)$', DropView.as_view()),
]
