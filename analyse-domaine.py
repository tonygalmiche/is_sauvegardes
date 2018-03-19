#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
import socket
import psycopg2
import psycopg2.extras
import time
import os
from datetime import datetime,timedelta
from syslog import syslog
import sys
from fonctions import *


#** Lecture des paramètres *****************************************************
if len(sys.argv)!=2:
    print "Fichier de configuration obligatoire en paramètre"
    exit()
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
#*******************************************************************************


#** Connexion à odoo-glpi ******************************************************
cnx,cr=connect2postgres(postgres)
#*******************************************************************************


SQL= """
    SELECT 
        io.site_id,
        io.service_id,
        ii.name identifiant,
        ii.mot_de_passe,
        io.name           ordinateur,
        io.id             ordinateur_id,
        iu.id             utilisateur_id,
        iu.mail,
        iu.login
    FROM is_identifiant  ii inner join is_ordinateur  io on ii.ordinateur_id=io.id
                            inner join is_utilisateur iu on ii.utilisateur_id=iu.id
    WHERE ii.name='admin' and ii.admin_ordinateur=True and io.site_id=1 
    ORDER BY io.name
"""
cr.execute(SQL)
rows = cr.fetchall()
for row in rows:
    print row["ordinateur"]
    response = os.system("ping -c 1 -t 1 " + row["ordinateur"]+" >/dev/null 2>&1")
    if response == 0:
        #** Liste des partages du poste ****************************************
        pwd=row["mot_de_passe"].replace('&','\&')
        cde="net rpc share -S "+row["ordinateur"]+" -W "+row["ordinateur"]+" -U admin%"+pwd+" 2>&1"
        lines = os.popen(cde).readlines()
        t=[]
        for line in lines:
            t.append(line.strip())
        partages=', '.join(t)
        if partages.find('Error')>0:
            partages=''
        if partages.find('failed')>0:
            partages=''
        #***********************************************************************


        if partages!='':
            #** Liste des utilisateurs du poste ********************************
            cde="net rpc user -S "+row["ordinateur"]+" -W "+row["ordinateur"]+" -U admin%"+pwd+" 2>&1"
            lines = os.popen(cde).readlines()
            t=[]
            for line in lines:
                t.append(line.strip())
            users=', '.join(t)
            if users.find('Error')>0:
                users=''
            if users.find('failed')>0:
                users=''
            #*******************************************************************


            #** Liste des administrateurs du poste *****************************
            cde="net rpc group members Administrateurs -S "+row["ordinateur"]+" -W "+row["ordinateur"]+" -U admin%"+pwd+" 2>&1"
            lines = os.popen(cde).readlines()
            t=[]
            for line in lines:
                t.append(line.strip())
            admins=', '.join(t)
            if admins.find('Error')>0:
                admins=''
            if admins.find('failed')>0:
                admins=''
            #*******************************************************************

            print u'- '+s(partages,80)
            print u'- '+s(users,80)
            print u'- '+s(admins,80)
            print u''

            #** Enregistrement dans odoo-glpi **********************************
            if cr:
                SQL="""
                    UPDATE is_ordinateur 
                    SET 
                        net_rpc_partages='"""+str(partages)+"""',
                        net_rpc_admins='"""+str(admins)+"""',
                        net_rpc_users='"""+str(users)+"""'
                    WHERE id="""+str(row['ordinateur_id'])+"""
                    """
                cr.execute(SQL)
                cnx.commit()
            #*******************************************************************










