#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
import time
import pytz
import psycopg2
import psycopg2.extras


#** Lecture des paramètres *****************************************************
resultat=[]
if len(sys.argv)!=2:
    resultat.append(u'Paramètre attendu : ')
    resultat.append(u'- Fichier de configuration')
    sortie(resultat)
fichier_de_config = sys.argv[1]
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
postgres  = p.get('postgres')
odoo_glpi = p.get('odoo_glpi')
nmap      = p.get('nmap')
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


#** Analyse du réseau avec nmap ************************************************
cde="nmap -n -sP "+nmap+" 2>&1"
lines=os.popen(cde).readlines()
IP=''
MAC=''
for line in lines:
    l=line.strip()
    t=l.split(' ')
    if len(t)>0:
        if t[0]=='Nmap':
            IP=t[4].strip()
        if t[0]=='MAC':
            MAC=t[2].strip()


            #** Recherche si cette adresse MAC existe déjà *********************
            SQL="""
                SELECT id,adresse_mac,adresse_ip
                FROM is_equipement_reseau
                WHERE adresse_mac='"""+MAC+"""'
                ORDER BY date_modification desc
                limit 1
            """
            cr.execute(SQL)
            rows = cr.fetchall()
            equipement_id=False
            for row in rows:
                equipement_id=row['id']
            #*******************************************************************


            #** Enregistrement dans odoo-glpi **********************************
            if postgres and odoo_glpi and cr:
                site_id       = odoo_glpi['site_id']
                mk=int(time.time())
                action='Maj'
                if equipement_id:
                    SQL="""
                        UPDATE is_equipement_reseau SET 
                            adresse_ip='"""+str(IP)+"""', 
                            date_modification='"""+str(datetime.utcfromtimestamp(mk))+"""'
                        WHERE id="""+str(equipement_id)+"""
                    """
                else:
                    action='Création'
                    SQL="""
                        INSERT INTO is_equipement_reseau (date_creation,date_modification,origine_modification,site_id,adresse_ip,adresse_mac,active) 
                        VALUES (
                            '"""+str(datetime.utcfromtimestamp(mk))+"""',
                            '"""+str(datetime.utcfromtimestamp(mk))+"""',
                            'nmap',
                            '"""+str(site_id)+"""', 
                            '"""+str(IP)+"""', 
                            '"""+str(MAC)+"""',
                            't'
                    ) """
                cr.execute(SQL)
                cnx.commit()
                print IP+' : '+MAC+' : '+action
            #*******************************************************************
#*******************************************************************************











