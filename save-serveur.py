#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
import time
import pytz
import psycopg2
import psycopg2.extras


#TODO : 
# - Récupérer l'espace disponible en local et sur le seagate
# - Rendre ce script opérationnel pour tous les serveurs (y compris pour OVH)


def sortie(resultat):
    #print resultat
    print u'\n'.join(resultat)
    exit()


resultat=[]
nb_anomalies=0

#** Lecture des paramètres *****************************************************
if len(sys.argv)!=3:
    resultat.append(u'Paramètres attendus : ')
    resultat.append(u'- Fichier de configuration')
    resultat.append(u'- Serveur de sauvegardes (seagate)')
    sortie(resultat)
fichier_de_config = sys.argv[1]
seagate           = sys.argv[2]
#*******************************************************************************


#** Lecture du fichier de configuration ****************************************
try:
    exec(open(fichier_de_config).read(), globals()) # le fichier de configuration doit contenir le tableau 'parametres'
except Exception, err:
    resultat.append(u'Fichier de configuration non valide : err='+err)
    sortie(resultat)
if 'parametres' not in globals():
    resultat.append(u"Le fichier de configuration ne contient pas de variable 'parametres'")
    sortie(resultat)
p=parametres
sauvegardes         = p.get('sauvegardes')
serveur             = p.get('serveur')
serveur_login       = p.get('serveur_login')
dossier_destination = p.get('dossier_destination')
dpkg                = p.get('dpkg')
postgres            = p.get('postgres')
odoo_glpi           = p.get('odoo_glpi')
#*******************************************************************************


#** Vérification que le seagate est disponible *********************************
destination=dossier_destination+serveur
cde="ssh "+serveur_login+"@"+seagate+" mkdir -p '"+destination+"' 2>&1"
lines=os.popen(cde).readlines()
if len(lines)>0:
    resultat.append(u"Serveur de sauvegardes (Seagate) '"+seagate+u"' non disponible !")
    sortie(resultat)
#*******************************************************************************


#** Sauvegarde de la liste des paquets *****************************************
if dpkg:
    cde="dpkg --get-selections > /root/dpkg--get-selections.txt"
    lines=os.popen(cde).readlines()
#*******************************************************************************


#** Sauvegarde *****************************************************************
mk1=int(time.time())
now = datetime.now(pytz.timezone('Europe/Paris')).strftime('%H:%M:%S')
resultat.append(now+u" : Debut de la sauvegarde sur '"+seagate+"' ***********************")
for s in sauvegardes:
    dossier   = s[0]
    name      = s[1]
    jour      = s[2]
    J=False
    if jour=='weekday':
        J=datetime.now().weekday()+1
    if jour=='day':
        J=datetime.now().day
    dest="/Sauvegardes/"+name
    if J:
        dest=dest+"-"+str(J)
    dest=dest+".tgz"

    #** Sauvegarde *************************************************************
    cde="tar -czf "+dest+" "+dossier+" 2>&1 | grep -v Suppression | grep -v socket"
    lines=os.popen(cde).readlines()
    err1=''
    if len(lines)>0:
        nb_anomalies=nb_anomalies+1
        err1=', '.join(lines)
        err1=unicode(err1,'utf-8')
    #***************************************************************************


    #** Copie sur le seagate ***************************************************
    cde="scp "+dest+" "+serveur_login+"@"+seagate+":"+dossier_destination+serveur+"/ 2>&1"
    lines=os.popen(cde).readlines()
    err2=''
    if len(lines)>0:
        nb_anomalies=nb_anomalies+1
        err2=u', '.join(lines)
    now = datetime.now(pytz.timezone('Europe/Paris')).strftime('%H:%M:%S')
    resultat.append(now+u" : - sauvegarde de '"+dossier+u"' dans '"+dest+u' '+err1+u' '+err2)
    #***************************************************************************

now = datetime.now(pytz.timezone('Europe/Paris')).strftime('%H:%M:%S')
resultat.append(now+u" : Fin de la sauvegarde sur '"+seagate+"' *************************")
#*******************************************************************************


#** Connexion à odoo-glpi ******************************************************

if postgres and odoo_glpi:
    cnx=False
    try:
        cnx = psycopg2.connect("dbname='"+postgres['dbname']+"' user='"+postgres['user']+"' host='"+postgres['host']+"' password='"+postgres['password']+"'")
    except Exception, e:
        resultat.append(u'ERREUR : Postgresql non disponible')
        sortie(resultat)
    cr = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#*******************************************************************************


#** Enregistrement dans odoo-glpi **********************************************
if postgres and odoo_glpi and cr:
    site_id       = odoo_glpi['site_id']
    ordinateur_id = odoo_glpi['ordinateur_id']
    mk2=int(time.time())
    temps=(mk2-mk1)
    r='\n'.join(resultat)
    r=r.replace("'","''")
    SQL="""
        INSERT INTO is_save_serveur (date,site_id, ordinateur_id, heure_debut,heure_fin,temps, nb_anomalies, resultat ) 
        VALUES (
            '"""+datetime.utcfromtimestamp(mk1).strftime('%Y-%m-%d')+"""',
            '"""+str(site_id)+"""', 
            '"""+str(ordinateur_id)+"""', 
            '"""+str(datetime.utcfromtimestamp(mk1))+"""',
            '"""+str(datetime.utcfromtimestamp(mk2))+"""',
            """+str(temps)+""",
            """+str(nb_anomalies)+""",
            '"""+r+"""'
    ) """
    cr.execute(SQL)
    cnx.commit()
#*******************************************************************************

sortie(resultat)



