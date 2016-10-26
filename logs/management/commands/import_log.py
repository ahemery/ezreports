import csv
import glob
import os
import pycurl
import re
import ldap3
from datetime import date, timedelta, datetime
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Max
from django.utils.text import slugify
from front.models import *

config = {
  "ldap": {
    "server": "ldap.univ-pau.fr",
    "user": "cn=consultplus,ou=admin,dc=univ-pau,dc=fr",
    "pwd": "uppaplus",
    "base": "ou=people,dc=univ-pau,dc=fr"
  },
  "ezpaarse": {
    "server": "http://ezpaarse.univ-pau.fr",
    "options": [
      "geoip: none",
      "Output-Fields: +datetime",
      "Crypted-Fields: none"
    ],
    "debug": "false"
  },
  "logpath": "/mnt/data/dev/scd/ezreports/proxy_logs/*.log",
  "csvpath": "/mnt/data/dev/scd/ezreports/csv/",
}


def querylaboratoire(ldap, name):

    name = name.replace("\\", "\\5C")
    name = name.replace("*", "\2A")
    name = name.replace("(", "\\28")
    name = name.replace(")", "\\29")
    name = name.replace("\0", "\\00")
    if not ldap.search(
            'ou=structures,dc=univ-pau,dc=fr',
            "(ou=" + name + ")",
            attributes=['supannCodeEntite']):
        return None

    return ldap.entries[0].supannCodeEntite.value


def connexions2sql(filename, sql):
    """
    Récupère les connexions à partir du fichier de log d'ezproxy
    et les stocke en base

    :param filename Nom du fichier à traiter
    :param sql  Cursor sql
    :return:
    """

    # Expression régulière pour les log d'ezproxy
    regex = "^(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3}) - " \
            "(?P<login>[0-9a-zA-Z]*) .*" \
            "\[(?P<datetime>.*)\].*connect\?session=.*&url=" \
            "https?://w*\.?(?P<url>.[^/]*)/(?P<path>.*) HTTP/1.1.*"
    login = re.compile(regex)

    # Ouvre le fichier
    with open(filename) as file:

        # Pour chaque lignes
        for line in file:

            # Ca match ?
            match = login.match(line)
            if not match:
                continue

            url = match.group("url")
            date = datetime.strptime(match.group("datetime"), '%d/%b/%Y:%H:%M:%S %z')

            # Insertion du lien si inconnu
            sql.execute(
                "INSERT INTO liens (url, slug, disabled) "
                "SELECT %(url)s, %(slug)s, 0 "
                "FROM (SELECT 1) as tmp "
                "WHERE NOT EXISTS(SELECT id FROM liens WHERE url = %(url)s or slug=%(slug)s) LIMIT 1 ",
                params={'url': url, 'slug': slugify(url)})

            # Insertion de l'utilisateur si inconnu
            sql.execute(
                "INSERT INTO utilisateurs (hash) SELECT md5(%(login)s) "
                "FROM (SELECT 1) as tmp "
                "WHERE NOT EXISTS(SELECT id FROM utilisateurs WHERE hash = md5(%(login)s)) LIMIT 1 ",
                params={'login': match.group("login")})

            # Insertion de la connexion
            sql.execute(
                "INSERT INTO connexions  "
                "SELECT NULL as id, %(date)s as date, %(time)s as time, md5(%(ip)s) as ip, "
                "l.id as lien_id, u.id as utilisateur_id  "
                "FROM utilisateurs u "
                "LEFT JOIN liens l           on l.url = %(url)s "
                "WHERE u.hash = md5(%(login)s) "
                "AND NOT EXISTS (SELECT utilisateur_id FROM connexions WHERE "
                "utilisateur_id = u.id AND lien_id = l.id AND date = %(date)s "
                "AND time = %(time)s AND ip = md5(%(ip)s))",
                params={'login': match.group("login"), 'url': url,
                        'date': date.strftime("%Y-%m-%d"), 'time': date.strftime("%H:%M:%S"),
                        'ip': match.group("ip")})

            connection.commit()


def log2csv(filename):
    """
    Converti un fichier log en csv en l'envoyant à ezPAARSE

    :param filename: Nom du fichier de log brut
    :param outputpath: chemin de sortie du fichier
    :return: Nom complet (chemin + nom_du_fichier) du fichier produit
    """

    ez = config['ezpaarse']

    now = datetime.now()
    print(str(now) + " Log 2 CSV : \"" + filename + "\"...")

    # Extrait le nom du fichier et son chemin d'accès
    path, file = os.path.split(filename)

    # Nom du fichier de sortie
    outfile = config['csvpath'] + os.path.splitext(file)[0] + '.csv'

    return outfile

    # On envoie le fichier de log à ezPAARSE
    with open(outfile, "wb") as handle:
        c = pycurl.Curl()
        if ez['debug'] == "true":
            c.setopt(c.VERBOSE, 1)
        if ez['options'] is not None:
            c.setopt(c.HTTPHEADER, ez['options'])
        c.setopt(c.URL, ez["server"])
        c.setopt(c.HTTPPOST, [(filename, (c.FORM_FILE, filename))])
        c.setopt(c.WRITEDATA, handle)
        c.perform()
        c.close()

    return outfile


def csv2sql(filename, sql):
    """
    Importe les fichiers CSV produits par ezPAARSE dans une base SQL

    :param filename: Nom du fichier CSV à importer
    :param sql      Connexion sql

    :return: Rien
    """

    # now = datetime.now()
    print(str(datetime.now()) + " CSV 2 SQL : \"" + filename + "\"")

    # Ouvre le fichier csv en lecture
    with open(filename, 'r') as csvfile:

        #
        # Connexion à l'annuaire LDAP
        server = ldap3.Server(config['ldap']['server'])
        ldap = ldap3.Connection(server,
            user=config['ldap']['user'],
            password=config['ldap']['pwd'],
            auto_bind=True)

        # Converti le fichier en format CSV
        for row in csv.DictReader(csvfile, delimiter=';'):
            #print(row)

            csvhash = ""
            for k, v in sorted(row.items()):
                csvhash += v

            # Variables
            dt = parse(row["datetime"])
            login = row["login"]

            # Insertion des clefs étrangères
            sql.execute("INSERT IGNORE INTO utilisateurs (hash) SELECT md5(%(login)s) "
                        "FROM (SELECT 1) as tmp "
                        "WHERE NOT EXISTS(SELECT id FROM utilisateurs WHERE hash = md5(%(login)s))",
                        params={'login': login})

            if row['publisher_name'] is not '':
                sql.execute("INSERT INTO editeurs (libelle, slug) SELECT %(libelle)s, %(slug)s "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM editeurs WHERE slug = %(slug)s) LIMIT 1 ",
                            params={'libelle': row["publisher_name"], 'slug': slugify(row['publisher_name'])})
            # todo: Faire le lien entre la ressource et l'éditeur lors de la création d'une nouvelle ressource
            if row['platform_name'] is not '':
                sql.execute("INSERT INTO ressources (libelle, slug) SELECT %(libelle)s, %(slug)s "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM ressources WHERE slug = %(slug)s) LIMIT 1 ",
                            params={'slug': slugify(row["platform_name"]), 'libelle': row["platform_name"]})
            if row['rtype'] is not '':
                sql.execute("INSERT INTO types (code) SELECT %(code)s "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM types WHERE code = %(code)s) LIMIT 1 ",
                            params={'code': row["rtype"]})
            if row['mime'] is not '':
                sql.execute("INSERT INTO formats (code) SELECT %(code)s "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM formats WHERE code = %(code)s) LIMIT 1 ",
                            params={'code': row["mime"]})

            # Insertions des consultations
            sql.execute("INSERT INTO consultations "
                        "(JOUR, HEURE, UTILISATEUR_ID, RESSOURCE_ID, EDITEUR_ID, TYPE_ID, FORMAT_ID, HOST, HASH) "
                        "SELECT %(jour)s, %(heure)s, u.id, r.id, e.id, t.id, f.id, %(host)s, sha1(%(hash)s) "
                        "FROM (SELECT 1) as tmp "
                        "LEFT JOIN utilisateurs u on u.hash = md5(%(login)s) "
                        "LEFT JOIN ressources r on r.slug = %(ressource)s "
                        "LEFT JOIN formats f on f.code = %(format)s "
                        "LEFT JOIN types t on t.code = %(type)s "
                        "LEFT JOIN editeurs e on e.slug = %(editeur)s "
                        "WHERE NOT EXISTS(SELECT id FROM consultations WHERE hash = sha1(%(hash)s)) "
                        "LIMIT 1 ",
                        {
                            'jour': dt.date(),
                            'heure': dt.time(),
                            'login': login,
                            'ressource': slugify(row["platform_name"]),
                            'editeur': slugify(row["publisher_name"]),
                            'type': row["rtype"],
                            'format': row["mime"],
                            'host': row["host"],
                            'hash': csvhash,
                        })

            ec_id = sql.lastrowid

            # On a déjà inséré cette ligne, donc on passe à la suivante
            if ec_id == 0:
                continue

            #
            # On récupère les informations LDAP du compte utilisateur
            if not ldap.search(
                'ou=people,dc=univ-pau,dc=fr',
                "(uid=" + login + ")",
                attributes=['supannEtuInscription', 'supannEntiteAffectationPrincipale', 'uppaCodeComp',
                            'uppaDrhComposante', 'uppaProfil', 'uppaDrhLaboratoire']):
                print("No ldap informations for \"" + login + "\"")
                continue

            # todo: Vilain hack, bouuh !
            infos = ldap.entries[0]._attributes
            if not infos:
                continue

            #
            # Converti le profil en tableau si ce n'est pas le cas
            profils = infos["uppaProfil"].values if "uppaProfil" in infos else ["VIDE"]
            for profil in profils:
                composante_libelle = None
                composante_code = None
                laboratoire = None
                laboratoire_code = None
                diplome_libelle = None
                diplome_code = None
                cursus_annee = None

                if profil == "VIDE":
                    composante_code = infos["uppaCodeComp"]
                    composante_libelle = infos["uppaDrhComposante"]

                #
                # Profil étudiant
                elif profil in ("ETU", "AE0", "AE1", "AE2", "AET", "AEP"):
                    if "supannEtuInscription" in infos:
                        # Eclate le champ supannEtuInscription
                        inscriptions = infos["supannEtuInscription"].values
                        for insc in inscriptions:
                            insc = insc.replace("[", "").split("]")
                            for d in insc:
                                d = d.split("=")
                                if d[0] == "cursusann":
                                    cursus_annee = d[1].replace("{SUPANN}", "")
                                if d[0] == "libDiplome":
                                    diplome_libelle = d[1]
                                if d[0] == "diplome":
                                    diplome_code = d[1].replace("{SISE}", "")
                    else:
                        cursus_annee = ""
                        diplome_libelle = infos["uppaDrhComposante"] if "uppaDrhComposante" in infos else None
                        if isinstance(diplome_libelle, list):
                            diplome_libelle = diplome_libelle[0]

                        diplome_code = infos["uppaCodeComp"] if "uppaCodeComp" in infos else None
                        if isinstance(diplome_code, list):
                            diplome_code = diplome_code[0]

                #
                # Profil personnel
                elif profil in ("PER", "DOC", "VAC", "INV", "APE", "HEB", "ANC", "APH", "CET", "EME", "LEC",
                                      "PVA", "PAD", "PEC", "STA", "ADM", "AP0", "PAR", "PPE", "ADC", "RSS", "AD0"):
                    #
                    # Composante
                    if "supannEntiteAffectationPrincipale" in infos:
                        composante_code = infos["supannEntiteAffectationPrincipale"].value

                        if len(infos["uppaCodeComp"]) > 1:
                            for id, code in enumerate(infos["uppaCodeComp"]):
                                if code == composante_code:
                                    composante_libelle = infos["uppaDrhComposante"][id]
                                    break
                        else:
                            composante_libelle = infos["uppaDrhComposante"].value

                    else:
                        composante_code = infos["uppaCodeComp"].value if "uppaCodeComp" in infos else ""
                        composante_libelle = infos["uppaDrhComposante"].value if "uppaDrhComposante" in infos else ""

                    #
                    # Laboratoire
                    if "uppaDrhLaboratoire" in infos:
                        laboratoire = infos["uppaDrhLaboratoire"][0].value \
                            if isinstance(infos["uppaDrhLaboratoire"], list) else infos["uppaDrhLaboratoire"].value

                        # todo: Par défaut, prend le premier enregistrement
                        if isinstance(laboratoire, list):
                            laboratoire = laboratoire[0]

                        laboratoire_code = querylaboratoire(ldap, laboratoire)
                else:
                    #print("Profil non géré : " + profil)
                    continue

                #
                # Insère les données manquants
                sql.execute("INSERT INTO profils (code) SELECT %(code)s "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM profils WHERE code = %(code)s) LIMIT 1 ",
                            params={'code': profil})

                if composante_code is not None and composante_code != 0 \
                        and composante_libelle is not None and composante_libelle != "":
                    sql.execute("INSERT INTO composantes (code, libelle) "
                                "SELECT %(code)s, %(libelle)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT code FROM composantes WHERE code = %(code)s) LIMIT 1 ",
                                {'code': composante_code, 'libelle': composante_libelle})

                if diplome_code is not None and diplome_libelle is not None:
                    sql.execute("REPLACE INTO diplomes (code, libelle) SELECT %(code)s, %(libelle)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM diplomes WHERE code = %(code)s) LIMIT 1 ",
                                {'code': diplome_code, 'libelle': diplome_libelle})

                if cursus_annee != "" and cursus_annee is not None:
                    sql.execute("INSERT INTO cursus (code) SELECT %(code)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM cursus WHERE code = %(code)s) LIMIT 1 ",
                                params={'code': cursus_annee})

                if laboratoire != "" and laboratoire is not None:
                    sql.execute("INSERT INTO laboratoires (code, libelle) SELECT %(code)s, %(libelle)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM laboratoires WHERE code = %(code)s "
                                "or libelle = %(libelle)s) LIMIT 1 ",
                                params={'code': laboratoire_code, 'libelle': laboratoire})

                sql.execute("INSERT IGNORE INTO meta "
                            "(consultation_id, profil_id, composante_id, laboratoire_id, diplome_id, cursus_id) "
                            "SELECT %(consultation)s, p.id, co.id, l.id, d.id, c.id "
                            "FROM profils p "
                            "LEFT JOIN laboratoires l on l.libelle = %(laboratoire)s "
                            "LEFT JOIN diplomes d on d.code = %(diplome)s "
                            "LEFT JOIN cursus c on c.code = %(cursus)s "
                            "LEFT JOIN composantes co on co.id = %(composante)s "
                            "WHERE p.code = %(profil)s",
                            {
                                'consultation': ec_id,
                                'profil': profil,
                                'composante': composante_code,
                                'laboratoire': laboratoire,
                                'diplome': diplome_code,
                                'cursus': cursus_annee
                            })

                connection.commit()


class Command(BaseCommand):
    args = '<team_id>'
    help = 'Process raw logs from the reverse proxy and import them in database'

    def add_arguments(self, parser):
        parser.add_argument('--min-date',
                            help="Everything before this date is ignored (dd/mm/yyyy)",
                            default=date.today() - timedelta(1),
                            required=False)

    def handle(self, *args, **options):
        # Si aucun argument, on prend depuis la dernière date en base
        if not options['min_date']:
            #
            # Date du dernier fichier traité
            query = Connexion.objects.all().aggregate(Max('date'))
            mindate = datetime(query['date__max'].year, query['date__max'].month, query['date__max'].day - 1)
        else:
            try:
                mindate = datetime.strptime(options['min_date'], '%d/%m/%Y',)
            except ValueError:
                raise CommandError('Invalide min-date format !')

        # Connexion SQL
        sql = connection.cursor()

        # Pour chaque fichier de log à traiter
        for logfile in sorted(glob.glob(config['logpath'])):

            # format du fichier 'ezproxy-YYYY.MM.DD.log'
            filename = os.path.split(logfile)[1]
            filedate = datetime.strptime(filename, 'ezproxy-%Y.%m.%d.log')

            if filedate < mindate:
                continue

            self.stdout.write("Processing '{}'".format(os.path.basename(logfile)))

            #
            # Importe les connexions
            #
            #connexions2sql(logfile, sql)

            #
            # Envoie les données au serveur EZPaarse
            #
            csvfile = log2csv(logfile)

            #
            # Envoie les données d'EZPaarse en base sql
            #
            csv2sql(csvfile, sql)




