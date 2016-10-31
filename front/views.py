from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404, render
from datetime import datetime, timedelta
from django.db.models import Count, F
from django.db import connection
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .forms import *
from django.http import HttpResponseForbidden
from django.template import RequestContext, loader


def forbidden(request, template='403.html'):
    """Default 403 handler"""
    t = loader.get_template(template)
    return HttpResponseForbidden(t.render(RequestContext(request)))


def login_view(request):

    # Déjà authentifié, on affiche son profile
    if request.user.is_authenticated():
        return redirect('dashboard')

    loginform = LoginForm(request.POST or None)
    if loginform.is_valid and request.method == "POST":
        data = loginform.data

        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user is not None and user.is_active:
            login(request, user)

            return redirect('dashboard')
        else:
            loginform.add_error('username', 'Invalid credentials !')

    return render(request, 'login.html', {
        'login': loginform,
    })


def logout_view(request):
    logout(request)

    return render(request, 'logout.html',
    {

    })


@login_required
def dashboard_view(request):

    ressources = Lien.objects.all()
    return render(request, 'dashboard.html',
    {
        'ressources': ressources,
    })


@login_required
def connexions_ressource_view(request, editeur=None, ressource=None):

    res = get_object_or_404(Ressource, slug=ressource)

    with connection.cursor() as cursor:

        # Connexions par année
        cursor.execute("""
        select year(c.date) as annee, month(c.date) as mois, count(*) as total
        from connexions c

        left join liens l        on l.id = c.lien_id
        left join ressources r   on r.id = l.ressource_id
        left join editeurs e     on e.id = r.editeur_id

        where e.slug = %s

        group by year(c.date), month(c.date)
        order by annee, mois""", [editeur])
        c = cursor.fetchall()

    conn = {}
    for r in c:
        if not r[0] in conn:
            conn[r[0]] = {1: 'null', 2: 'null', 3: 'null', 4: 'null', 5: 'null', 6: 'null',
                          7: 'null', 8: 'null', 9: 'null', 10: 'null', 11: 'null', 12: 'null'}
        conn[r[0]][r[1]] = r[2]

    return render(request, 'connexions/ressource.html', {
        'connexions': conn,
        'editeur': Editeur.objects.get(slug=editeur),
        'ressource': res,
    })


@login_required
def connexions_editeur_view(request, editeur=None):

    ed = get_object_or_404(Editeur, slug=editeur)

    ressources = Connexion.objects\
        .values('lien__ressource')\
        .filter(date__year=str(datetime.now().year))\
        .filter(lien__ressource__editeur=ed)\
        .annotate(total=Count('lien__ressource'))\
        .annotate(ressource=F('lien__ressource__libelle'))\
        .annotate(ressource_slug=F('lien__ressource__slug'))\
        .order_by('-total')[:10]

    with connection.cursor() as cursor:

        # Connexions par année
        cursor.execute("""
        select year(c.date) as annee, month(c.date) as mois, count(*) as total
        from connexions c

        left join liens l        on l.id = c.lien_id
        left join ressources r   on r.id = l.ressource_id
        left join editeurs e     on e.id = r.editeur_id

        where e.slug = %s

        group by year(c.date), month(c.date)
        order by annee, mois""", [editeur])
        res = cursor.fetchall()

    conn = {}
    for r in res:
        if not r[0] in conn:
            conn[r[0]] = {1: 'null', 2: 'null', 3: 'null', 4: 'null', 5: 'null', 6: 'null',
                          7: 'null', 8: 'null', 9: 'null', 10: 'null', 11: 'null', 12: 'null'}
        conn[r[0]][r[1]] = r[2]

    return render(request, 'connexions/editeur.html', {
        'editeur': ed,
        'connexions': conn,
        'ressources': ressources,
    })


@login_required
def connexions_index_view(request):

    tops = Connexion.objects\
        .values('lien__ressource')\
        .filter(date__year=str(datetime.now().year))\
        .annotate(total=Count('lien__ressource'))\
        .annotate(ressource=F('lien__ressource__libelle'))\
        .annotate(ressource_slug=F('lien__ressource__slug'))\
        .annotate(editeur=F('lien__ressource__editeur__libelle'))\
        .annotate(editeur_slug=F('lien__ressource__editeur__slug'))\
        .order_by('-total')

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
        HAVING editeur_ratio > 1.5
        ORDER BY editeur_ratio desc
        """, [2016])
        res = cursor.fetchall()

        cursor.execute("""
        select year(c.date) as annee, month(c.date) as mois, count(*) as total
        from connexions c

        group by year(c.date), month(c.date)
        order by annee, mois""")
        res2 = cursor.fetchall()

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

    conn = {}
    for r in res2:
        if not r[0] in conn:
            conn[r[0]] = {1: 'null', 2: 'null', 3: 'null', 4: 'null', 5: 'null', 6: 'null',
                          7: 'null', 8: 'null', 9: 'null', 10: 'null', 11: 'null', 12: 'null'}
        conn[r[0]][r[1]] = r[2]

    return render(request, 'connexions/index.html', {
        # 'start': start,
        'tops': tops,
        'donut': sorted(donut.items(), key=lambda x: x[1]['total'], reverse=True),
        'connexions': conn,
    })


@login_required
def consultations_view(request):

    return render(request, 'consultations.html',
    {

    })


@login_required
def ressources_view(request):

    liens = Lien.objects.all().order_by('url')
    editeurs = Editeur.objects.all().order_by('libelle')

    return render(request, 'ressources.html',
    {
        'liens': liens,
        'editeurs': editeurs,
    })


@login_required
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


@login_required
def params_view(request):

    return render(request, 'params.html',
    {

    })


@login_required
def editeur_view(request, slug):

    editeur = get_object_or_404(Editeur, slug=slug)
    ressources = Ressource.objects.filter(editeur=editeur).order_by('libelle')

    return render(request, 'editeur.html',
    {
        'editeur': editeur,
        'ressources': ressources,
    })


@login_required
def editeurs_view(request):

    editeurs = Editeur.objects.all() \
        .annotate(ressources=Count('ressource')) \
        .order_by('libelle')
    liens = Lien.objects \
        .values('url', 'slug') \
        .filter(disabled=False, ressource=None)\
        .order_by('slug')

    return render(request, 'editeurs.html', {
        'editeurs': editeurs,
        'liens': liens,
    })


@login_required
def lien_view(request, slug):

    instance = get_object_or_404(Lien, slug=slug)
    form = LienForm(request.POST or None, instance=instance)
    if form.is_valid() and request.method == "POST":
        form.save()

    return render(request, 'lien.html', {
        'instance': instance,
        'form': form,
    })


@login_required
def liens_view(request):
    liens = Lien.objects.all().order_by('url')

    return render(request, 'lien.html',
    {
        'liens': liens,
    })


@login_required
def counter_view(request):

    return render(request, 'counter.html',
    {
    })


