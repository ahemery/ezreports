from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404, render
from datetime import datetime, timedelta
from django.db.models import Count, F
from django.db import connection
from django.db.models.functions import TruncMonth
import operator

def login_view(request):
    return render(request, 'login.html',
    {

    })


def logout_view(request):
    return render(request, 'logout.html',
    {

    })


def dashboard_view(request):

    ressources = Lien.objects.all()
    return render(request, 'dashboard.html',
    {
        'ressources': ressources,
    })


def connexions_view(request):

    start = datetime.now() - timedelta(days=90)
    connexions = Connexion.objects \
        .values('date')\
        .filter(date__gte=start)\
        .annotate(total=Count('date'))\
        .order_by('date')

    tops = Connexion.objects\
        .values('lien__ressource')\
        .filter(date__year=str(datetime.now().year))\
        .annotate(total=Count('lien__ressource'))\
        .annotate(ressource=F('lien__ressource__libelle'))\
        .annotate(ressource_slug=F('lien__ressource__slug'))\
        .annotate(editeur=F('lien__ressource__editeur__libelle'))\
        .annotate(editeur_slug=F('lien__ressource__editeur__slug'))\
        .order_by('-total')[:10]

    with connection.cursor() as cursor:
        cursor.execute("""
        select e.id as editeur_id, e.libelle as editeur, COUNT(c.id) AS editeur_total,
        sub.id as ressource_id, sub.libelle as ressource, sub.connexions as ressource_total,
        round(sub.connexions / total.total * 100, 2) as ratio, total.total as ressource_ratio,
        round(count(c.id) / total.total * 100, 2) as editeur_ratio
        FROM editeurs e

        LEFT JOIN `ressources` r          ON e.id = r.editeur_id
        LEFT JOIN `liens` l               ON r.id = l.ressource_id
        LEFT JOIN `connexions` c          ON l.id = c.lien_id

        LEFT JOIN
        (
                SELECT r.id, r.libelle, r.editeur_id, count(c.id) AS connexions, year(c.date) as year
                FROM ressources r

                LEFT JOIN liens l           ON (r.id = l.ressource_id)
                LEFT JOIN connexions c ON (l.id = c.lien_id)

                GROUP BY r.id, year(c.date)
        ) sub                              ON sub.editeur_id = e.id
        								   and sub.year = year(c.date)

        LEFT JOIN
        (
	        select COUNT(c.id) AS total, year(c.date) as year
	        FROM editeurs e

	        LEFT JOIN `ressources` r          ON e.id = r.editeur_id
	        LEFT JOIN `liens` l               ON r.id = l.ressource_id
	        LEFT JOIN `connexions` c          ON l.id = c.lien_id

			  GROUP BY year(c.date)

        ) as total on total.year = year(c.date)

        WHERE year(c.date) = %s

        GROUP BY e.id , sub.id, total.total, sub.connexions
        HAVING ratio > 1
        ORDER BY ratio desc
        """, [2016])
        res = cursor.fetchall()

    donut = {}
    for r in res:
        if not r[0] in donut:
            donut[r[0]] = {
                'editeur': r[1],
                'total': r[2],
                'ratio': r[8],
                'ressources': {}
            }

        donut[r[0]]['ressources'][r[3]] = {
            'libelle': r[4],
            'total': r[5],
            'ratio': r[6],
        }

    return render(request, 'connexions.html',
    {
        'connexions': connexions,
        'start': start,
        'tops': tops,
        'donut': sorted(donut.items(), key=lambda x: x[1]['total'], reverse=True),
    })


def consultations_view(request):

    return render(request, 'consultations.html',
    {

    })


def ressources_view(request):

    liens = Lien.objects.all().order_by('url')
    editeurs = Editeur.objects.all().order_by('libelle')

    return render(request, 'ressources.html',
    {
        'liens': liens,
        'editeurs': editeurs,
    })


def ressource_view(request, slug):

    ressource = get_object_or_404(Ressource, slug=slug)
    liens = Lien.objects.filter(ressource=ressource).order_by('url')
    editeur = Editeur.objects.get(id=ressource.editeur_id)

    return render(request, 'ressource.html',
    {
        'ressource': ressource,
        'editeur': editeur,
        'liens': liens,
    })


def params_view(request):

    return render(request, 'params.html',
    {

    })


def editeur_view(request, slug):

    editeur = get_object_or_404(Editeur, slug=slug)
    ressources = Ressource.objects.filter(editeur=editeur).order_by('libelle')

    return render(request, 'editeur.html',
    {
        'editeur': editeur,
        'ressources': ressources,
    })


def editeurs_view(request):

    editeurs = Editeur.objects.all() \
        .annotate(ressources=Count('ressource__editeur')) \
        .order_by('libelle')
    liens = Lien.objects.filter(ressource=None).order_by('url')

    return render(request, 'editeurs.html',
    {
        'editeurs': editeurs,
        'liens': liens,
    })


def lien_view(request, slug):
    lien = get_object_or_404(Lien, slug=slug)

    return render(request, 'lien.html',
    {
        'lien': lien,
    })


def liens_view(request):
    liens = Lien.objects.all().order_by('url')

    return render(request, 'lien.html',
    {
        'liens': liens,
    })

