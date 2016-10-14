
from django.conf.urls import url
from . import views
from django.views.generic import TemplateView
from django.template import RequestContext
from django.shortcuts import render_to_response


#
# Gestion du 404
#
def handler404(request):
    response = render_to_response('404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


urlpatterns = [
    url(r'^$', views.dashboard_view, name='dashboard'),
    url(r'^connexions/$', views.connexions_view, name='connexions'),
    url(r'^consultations/$', views.consultations_view, name='consultations'),
    url(r'^imports/$', views.imports_view, name='imports'),
    url(r'^params', views.params_view, name='params'),

    url(r'^plateforme/(?P<slug>[\w\-]+)?/$', views.plateforme_view, name='plateforme'),
    url(r'^base/(?P<slug>[\w\-]+)?/$', views.base_view, name='base'),

    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
]