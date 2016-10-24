import glob
from datetime import datetime
import re
import os
from django.db import connection
from front.models import *
from django.db.models import Max
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify


config = {
  "ldap": {
    "server": "ldap.univ-pau.fr",
    "dn": "cn=consultplus,ou=admin,dc=univ-pau,dc=fr",
    "pw": "uppaplus",
    "code": "ou=people,dc=univ-pau,dc=fr"
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
  "path": "/mnt/data/dev/scd/ezreports/proxy_logs/*.log",
}


def processconnexions(handle):
    """
    Récupère les connexions à partir du fichier de log d'ezproxy

    :param handle Handle du fichier à traiter
    :return:
    """

    # Expression régulière pour les log d'ezproxy
    regex = "^(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3}) - " \
            "(?P<login>[0-9a-zA-Z]*) .*" \
            "\[(?P<datetime>.*)\].*connect\?session=.*&url=" \
            "https?://w*\.?(?P<url>.[^/]*)/(?P<path>.*) HTTP/1.1.*"
    login = re.compile(regex)

    # # Pour chaque fichier de log à traiter
    # for logfile in sorted(glob.glob(path)):
    #
    #     # format du fichier 'ezproxy-YYYY.MM.DD.log'
    #     filename = os.path.split(logfile)[1]
    #     filedate = datetime.strptime(filename, 'ezproxy-%Y.%m.%d.log')
    #
    #     if filedate < mindate:
    #         continue
    #
    #     stdout.write("Processing connections from '{}'".format(os.path.basename(logfile)))
    #
    #     # Ouvre le fichier
    #     with open(logfile) as handle:
    #
    with connection.cursor() as cursor:

        # Pour chaque lignes
        for line in handle:

            # Ca match ?
            match = login.match(line)
            if match:
                url = match.group("url")
                date = datetime.strptime(match.group("datetime"), '%d/%b/%Y:%H:%M:%S %z')

                # Insertion du lien si inconnu
                cursor.execute(
                    "INSERT INTO liens (url, slug, disabled) "
                    "SELECT %(url)s, %(slug)s, 0 "
                    "FROM (SELECT 1) as tmp "
                    "WHERE NOT EXISTS(SELECT id FROM liens WHERE url = %(url)s or slug=%(slug)s) LIMIT 1 ",
                    params={'url': url, 'slug': slugify(url)})

                # Insertion de l'utilisateur si inconnu
                cursor.execute("INSERT INTO utilisateurs (hash) SELECT md5(%(login)s) "
                        "FROM (SELECT 1) as tmp "
                        "WHERE NOT EXISTS(SELECT id FROM utilisateurs WHERE hash = md5(%(login)s)) LIMIT 1 ",
                    params={'login': match.group("login")})

                # Insertion de la connexion
                cursor.execute("INSERT INTO connexions  "
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


def log2csv(filename, outputpath):
    """
    Converti un fichier log en csv en l'envoyant à ezPAARSE

    :param filename: Nom du fichier de log brut
    :param outputpath: chemin de sortie du fichier
    :return: Nom complet (chemin + nom_du_fichier) du fichier produit
    """

    ez = config['ezpaarse']

    now = datetime.datetime.now()
    print(str(now) + " Log 2 CSV : \"" + filename + "\"...")

    # Extrait le nom du fichier et son chemin d'accès
    path, file = os.path.split(filename)

    # Nom du fichier de sortie
    outfile = outputpath + os.path.splitext(file)[0] + '.csv'

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

    # print("CSV saved to \"" + outfile + "\"")

    return outfile


def csv2sql(filename):
    """
    Importe les fichiers CSV produits par ezPAARSE dans une base SQL

    :param filename: Nom du fichier CSV à importer

    :return: Rien
    """

    now = datetime.datetime.now()
    print(str(now) + " CSV 2 SQL : \"" + filename + "\"")

    #
    # Connexion à la base MySQL
    try:
        conn = mysql.connector.connect(**config['sql'])
        sql = conn.cursor()

        # Ouvre le fichier csv en lecture
        with open(filename, 'rb') as csvfile:

            #
            # Connexion à l'annuaire LDAP
            ldap = LDAPSingle(config["ldap"])
            ldap.setBaseDN(config["ldap"]["base"])

            # Converti le fichier en format CSV
            for row in csv.DictReader(csvfile, delimiter=';'):

                # Variables
                dt = parse(row["datetime"])
                login = row["login"]

                # Insertion des clefs étrangères
                sql.execute("INSERT IGNORE INTO utilisateurs (hash) SELECT md5(%(login)s) "
                            "FROM (SELECT 1) as tmp "
                            "WHERE NOT EXISTS(SELECT id FROM utilisateurs WHERE hash = md5(%(login)s))",
                            params={'login': login})

                if row['platform'] != "" and row['platform'] is not None:
                    sql.execute("INSERT INTO plateformes (code, libelle) SELECT %(code)s, %(libelle)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM plateformes WHERE code = %(code)s) LIMIT 1 ",
                                params={'code': row["platform"], 'libelle': row["platform_name"]})
                if row['rtype'] != "" and row['rtype'] is not None:
                    sql.execute("INSERT INTO types (code) SELECT %(code)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM types WHERE code = %(code)s) LIMIT 1 ",
                                params={'code': row["rtype"]})
                if row['mime'] != "" and row['mime'] is not None:
                    sql.execute("INSERT INTO formats (code) SELECT %(code)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM formats WHERE code = %(code)s) LIMIT 1 ",
                                params={'code': row["mime"]})
                if row['publisher_name'] != "" and row['publisher_name'] is not None:
                    sql.execute("INSERT INTO editeurs (libelle) SELECT %(libelle)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM editeurs WHERE libelle = %(libelle)s) LIMIT 1 ",
                                params={'libelle': row["publisher_name"]})

                # Insertions des EC
                try:
                    hash = ""
                    for k, v in enumerate(row):
                        hash += row[v]

                    sql.execute("INSERT INTO ec "
                                "(DATE, TIME, LOGIN, PLATFORME_ID, EDITEUR_ID, TYPE_ID, FORMAT_ID, HOST, HASH) "
                                "SELECT %(date)s, %(time)s, u.id, p.id, e.id, t.id, m.id, "
                                "%(host)s, sha1(%(hash)s) "
                                "FROM (SELECT 1) as tmp "
                                "LEFT JOIN utilisateurs u on u.hash = md5(%(login)s) "
                                "LEFT JOIN plateformes p on p.code = %(platform)s "
                                "LEFT JOIN formats m on m.code = %(format)s "
                                "LEFT JOIN types t on t.code = %(rtype)s "
                                "LEFT JOIN editeurs e on e.libelle = %(publisher)s "
                                "WHERE NOT EXISTS(SELECT id FROM ec WHERE hash = sha1(%(hash)s)) "
                                "LIMIT 1 ",
                                {
                                    'date': dt.date(),
                                    'time': dt.time(),
                                    'login': login,
                                    'platform': row["platform"],
                                    'platform_name': row["platform_name"],
                                    'publisher': row["publisher_name"],
                                    'rtype': row["rtype"],
                                    'format': row["mime"],
                                    'host': row["host"],
                                    'hash': hash,
                                })
                except mysql.connector.Error as err:
                    print("Something went wrong: {}".format(err))
                    continue

                ec_id = sql.lastrowid

                # On a déjà inséré cette ligne, donc on passe à la suivante
                if ec_id == 0:
                    continue

                #
                # On récupère les informations LDAP du compte utilisateur
                infos = ldap.getInfos("uid=" + login, ['supannEtuInscription', 'supannEntiteAffectationPrincipale',
                                                       'uppaCodeComp', 'uppaDrhComposante', 'uppaProfil', 'uppaDrhLaboratoire'])
                if len(infos) != 1:
                    print("No ldap informations for \"" + login + "\"")
                    continue
                infos = infos[0]

                #
                # Converti le profil en tableau si ce n'est pas le cas
                profils = infos["uppaProfil"] if infos.has_key("uppaProfil") else ["VIDE"]       # Cas des comptes sans profil
                profils = profils if isinstance(profils, list) else [profils]
                for profil in profils:
                    composante_libelle = None
                    composante_code = None
                    laboratoire = None
                    diplome_libelle = None
                    diplome_code = None
                    cursus_annee = None

                    if profil == "VIDE":
                        composante_code = infos["uppaCodeComp"]
                        composante_libelle = infos["uppaDrhComposante"]

                        pass

                    #
                    # Profil étudiant
                    elif profil in ("ETU", "AE0", "AE1", "AE2", "AET", "AEP"):
                        if infos.has_key("supannEtuInscription"):
                            # Eclate le champ supannEtuInscription
                            inscription = infos["supannEtuInscription"][0] if isinstance(infos["supannEtuInscription"], list) else infos["supannEtuInscription"]
                            inscription = inscription.replace("[", "").split("]")
                            for insc in inscription:
                                d = insc.split("=")
                                if d[0] == "cursusann":
                                    cursus_annee = d[1].replace("{SUPANN}", "")
                                if d[0] == "libDiplome":
                                    diplome_libelle = d[1]
                                if d[0] == "diplome":
                                    diplome_code = d[1].replace("{SISE}", "")
                        else:
                            cursus_annee = ""
                            diplome_libelle = infos["uppaDrhComposante"] if infos.has_key("uppaDrhComposante") else ""
                            if isinstance(diplome_libelle, list):
                                diplome_libelle = diplome_libelle[0]

                            diplome_code = infos["uppaCodeComp"] if "uppaCodeComp" in infos else ""
                            if isinstance(diplome_code, list):
                                diplome_code = diplome_code[0]

                    #
                    # Profil personnel
                    elif profil in ("PER", "DOC", "VAC", "INV", "APE", "HEB", "ANC", "APH", "CET", "EME", "LEC", "PVA",
                                    "PAD", "PEC", "STA", "ADM", "AP0", "PAR", "PPE", "ADC", "RSS", "AD0"):
                        # Trouve la composante en fonction de supannEntiteAffectationPrincipale
                        if infos.has_key("supannEntiteAffectationPrincipale"):
                            composante_code = infos["supannEntiteAffectationPrincipale"]

                            if isinstance(infos["uppaCodeComp"], list):
                                for id, code in enumerate(infos["uppaCodeComp"]):
                                    if code == composante_code:
                                        composante_libelle = infos["uppaDrhComposante"][id]
                                        break
                            else:
                                composante_libelle = infos["uppaDrhComposante"]

                        else:
                            composante_code = infos["uppaCodeComp"] if infos.has_key("uppaCodeComp") else ""
                            composante_libelle = infos["uppaDrhComposante"] if infos.has_key("uppaDrhComposante") else ""

                        #
                        # Laboratoire
                        if infos.has_key("uppaDrhLaboratoire"):
                            laboratoire = infos["uppaDrhLaboratoire"][0] if isinstance(infos["uppaDrhLaboratoire"], list) else infos["uppaDrhLaboratoire"]

                    else:
                        #print("Profil non géré : " + profil)
                        continue

                    #
                    # Insère les données manquants
                    sql.execute("INSERT INTO profils (code) SELECT %(code)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM profils WHERE code = %(code)s) LIMIT 1 ",
                                params={'code': profil})

                    if composante_code is not None and composante_code != 0 and composante_libelle is not None and composante_libelle != "":
                        sql.execute("REPLACE INTO composantes (id, libelle) VALUES (%(id)s, %(libelle)s)",
                                    {'id': composante_code, 'libelle': composante_libelle})

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
                        sql.execute("INSERT INTO laboratoires (libelle) SELECT %(libelle)s "
                                    "FROM (SELECT 1) as tmp "
                                    "WHERE NOT EXISTS(SELECT id FROM laboratoires WHERE libelle = %(libelle)s) LIMIT 1 ",
                                    params={'libelle': laboratoire})

                    sql.execute("INSERT IGNORE INTO meta (ec_id, profil_id, composante_id, laboratoire_id, diplome_id, cursus_id) "
                                "SELECT %(ec_id)s, p.id, co.id, l.id, d.id, c.id "
                                "FROM profils p "
                                "LEFT JOIN laboratoires l on l.libelle = %(laboratoire)s "
                                "LEFT JOIN diplomes d on d.code = %(diplome)s "
                                "LEFT JOIN cursus c on c.code = %(cursus)s "
                                "LEFT JOIN composantes co on co.id = %(composante)s "
                                "WHERE p.code = %(profil)s",
                                {
                                    'ec_id': ec_id,
                                    'profil': profil,
                                    'composante': composante_code,
                                    'laboratoire': laboratoire,
                                    'diplome': diplome_code,
                                    'cursus': cursus_annee
                                })

                    conn.commit()

        sql.close()
        conn.close()

    except mysql.connector.Error as err:
        print(err)
        exit()


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

            # Pour chaque fichier de log à traiter
            for logfile in sorted(glob.glob(config['path'])):

                # format du fichier 'ezproxy-YYYY.MM.DD.log'
                filename = os.path.split(logfile)[1]
                filedate = datetime.strptime(filename, 'ezproxy-%Y.%m.%d.log')

                if filedate < mindate:
                    continue

                self.stdout.write("Processing '{}'".format(os.path.basename(logfile)))

                # Ouvre le fichier
                with open(logfile) as handle:

                    #
                    # Importe les connexions
                    #
                    processconnexions(handle)

                    #
                    # Envoie les données au serveur EZPaarse
                    #
                    handle.seek(offset=0)




