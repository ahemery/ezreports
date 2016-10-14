
from django.conf.urls import url
from . import views
from django.views.generic import TemplateView


urlpatterns = [
    url(r'^$', views.dashboard_view, name='dashboard'),
    url(r'^connexions/$', views.connexions_view, name='connexions'),
    url(r'^consultations/$', views.consultations_view, name='consultations'),
    url(r'^imports/$', views.imports_view, name='imports'),
]