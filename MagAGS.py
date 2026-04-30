#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Programme de suivi de l'état de charge SOC de la batterie et contrôle 
# de la génératrice selon des seuils minimum et maxmimum.
# Ce programme a été fait pour remplacer le module ME-BMK de Magnum-Energy
# qui a des problèmes à effectuer le suivi du SOC de la batterie.
#
# Auteur: Daniel Cote, Mars 2025
# 

import logging
import sqlite3
import time
from datetime import date, datetime
from conf import getconf
from relay import Relay
from manage_gen import manage_gen

# Convertit les niveaux de sévérité en leur valeurs de type int
# Retourne 20 par défaut si aucun match.

def llevel(level):
    ''' Convertit les niveaux de sévérité en leur valeurs de type int
        Retourne 20 par défaut si aucun match.
    '''
    if level == 'DEBUG':
        return 10
    if level == 'INFO':
        return 20
    if level == 'WARNING':
        return 30
    if level == 'ERROR':
        return 40
    if level == 'CRITICAL':
        return 50
    return 20

# Détermine si nous sommes en exercice.
def is_time2exercise_old() -> bool:
    """Retourne True si nous sommes dans la période d'exercice."""
    d = date.today()
    d = datetime(2026, 5, 3) # Force au premier dimanche du mois de mai 2026
    t = time.localtime()
#    t = time.localtime(1777852863.0) # Force l'heure à Sun May  3 20:01:03 2026
    t = time.localtime(1777852863.0) # Force l'heure à Sun May  3 20:15:03 2026
#    t = time.localtime(1777852863.0) # Force l'heure à Sun May  3 20:20:03 2026
    t1 = 0
    if d.weekday() == 6 and d.day <= 7: # weekday() retourne 6 pour dimanche, et si le jour est <= 7, c'est le premier
        print("On est bien le premier dimanche du mois...")
        if t.tm_hour == 20:
            print("Il est bien passé 20h...")
            if t1 == 0:
                t1 = time.time()
            if time.time() - t1 < 1200:
                print(f"On est bien dans la période de 20 minutes...{time.time() - t1}")
                return True
            else:
                t1 = 0
    return False

def is_time2exercise(t: str, duration: int = 1200) -> bool:
    # --- Validation du format 'HHMM' ---
    if len(t) != 4 or not t.isdigit():
        return False
    hh, mm = int(t[:2]), int(t[2:])
    if hh > 23 or mm > 59:
        return False

    today = date.today()
    now = datetime.now()

    # --- Condition 1 : premier dimanche du mois ---
    if not (today.weekday() == 6 and today.day <= 7):
        return False

    # --- Condition 2 : l'heure t est atteinte ---
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if now < target:
        return False

    # --- Condition 3 : moins de 1200 secondes (20 min) depuis t ---
    elapsed = (now - target).total_seconds()
    return elapsed < duration

def cvtstate(state):
    if state == True:
        return 'ON'
    return 'OFF'

def getcurrentstate(relay):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if relay.state(1) is True:
                return 'ON'
            else:
                return 'OFF'
        except Exception as e:
            log.error(f"Erreur lors de la lecture de l'état du relais (tentative {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Attendre 1 seconde avant de réessayer
            else:
                # Après tous les essais, tenter une reconnexion
                return "ERROR"
    return "ERROR"


def reconnect_relay(relay, max_attempts=3, delay=2):
    """
    Tente de reconnecter le relais en fermant proprement l'ancienne connexion
    et en en créant une nouvelle - équivalent à un arrêt/redémarrage du programme
    """
    for attempt in range(max_attempts):
        try:
            log.warning(f"Tentative de reconnexion au relais ({attempt + 1}/{max_attempts})")
            
            # Fermer proprement l'ancienne connexion (équivalent à l'arrêt du programme)
            try:
                if relay is not None:
                    relay.close()
                    log.debug("Ancienne connexion au relais fermée")
            except Exception as e:
                log.debug(f"Erreur lors de la fermeture (ignorée): {e}")
            
            # Petit délai pour laisser l'USB se stabiliser
            time.sleep(delay)
            
            # Créer une nouvelle connexion (équivalent au redémarrage du programme)
            new_relay = Relay(idVendor=0x16c0, idProduct=0x05df)
            
            # Tester la nouvelle connexion
            new_relay.state(0, on=False)
            test_state = new_relay.state(1)  # Lecture de test
            
            log.info("Relais reconnecté avec succès")
            return new_relay
            
        except Exception as e:
            log.error(f"Échec de reconnexion (tentative {attempt + 1}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                log.critical("Toutes les tentatives de reconnexion ont échoué")
    
    return None


# ===========Programme Principal=======================================================

#configure logging.
fmt = '%(asctime)s %(levelname)s %(lineno)s %(message)s'
logging.basicConfig(level=getconf('ll'), filename=getconf('lf'), format=fmt)
log = logging.getLogger('MagAGS')

log.info("Début du programme")


logl = getconf('ll')
log.setLevel(llevel(logl))
log.info(f"Log level= {logl}")
# Backup des paramêtres de configuration
loglb = logl

# Détermination de l'enregistrement des conditions d'opération
ftype = getconf('ftype')

# Intervale de temps
interval = 60 # boucle aux 60 secondes

# Condition de la boucle sans fin. Si la valeur change, on sort de la boucle.
cmd = 'RUN'

frun = None

# Contient la réponse de la décision s'il faut démarrer la génératrice
# ou non em mode AUTO
resp = ''

# Connexion à la base de données
conn = sqlite3.connect("../monitormidnite/monitormidnite.db")
curs = conn.cursor()

# Objet relay
relay = Relay(idVendor=0x16c0, idProduct=0x05df)
# Turn all switches off
relay.state(0, on=False)

relay_error_count = 0
max_relay_errors = 5  # Reconnecter après 5 erreurs consécutives

exercise_gen = False # Détermine si la génératrice est en exercice True=oui, False=non

while cmd == 'RUN':
    start = time.time()
    log.debug("Looping... %s", time.ctime())

    logl = getconf('ll')
    log.setLevel(llevel(logl))
    if logl != loglb:
        log.info(f"Changement de log level de {loglb} à {logl}")
        loglb = logl

    # Contrôle de l'exécution du programme
    cmd = getconf('cmd')

# Contrôle de l'exercice de la génératrice
# La génératrice est démarrée chaque premier dimanche du mois à exh et pour une durée de exd.
    exercise = getconf('ex') # ON ou OFF
    exercise_time = getconf('exh') # Heure en format HHMM
    exercise_duration = getconf('exd')

    if exercise == 'ON': # L'option d'exercice est active
        # Sommes-nousen exercise ?
        if is_time2exercise(exercise_time, 1200):
            log.info(f"Nous sommes le premier dimanche du mois et il est passé {exercise_time}")
            if exercise_gen == False:
                relay.state(1, on=True)
                log.debug("Période d'exercice activée...")
                exercise_gen=True
                continue # Rien ne sert de voir si il faut démarrer la génératrice selon le SOC
        else:
            if exercise_gen == True:
                relay.state(1, on=False)
                log.debug("Période d'exercice terminée...")
                exercise_gen=False


# Contröle de la génératrice selon le SOC (State Of Charge)
# La génératrice démarre lorsque le SOC décroit et atteint SOCmin et arrête lorsque SOCmax est atteint

    # Valeurs des SOC min et max
    SOCmin = int(getconf('SOCsetpoints')[0:2])
    SOCmax = int(getconf('SOCsetpoints')[2:4])

    ftype = getconf('ftype')
    ftxt = getconf('ftxt')
    fSQLite = getconf('fSQLite')

    genctrl = getconf('genctrl')

# Vérifier si le relais a besoin d'être reconnecté
    if relay_error_count >= max_relay_errors:
        log.warning("Trop d'erreurs de relais détectées, tentative de reconnexion complète...")
        new_relay = reconnect_relay(relay, max_attempts=3, delay=3)  # Passer l'objet relay existant
        if new_relay is not None:
            relay = new_relay
            relay_error_count = 0
            log.info("Relais reconnecté - reprise normale des opérations")
        else:
            log.critical("Impossible de reconnecter le relais après plusieurs tentatives")
            # Option: envoyer une alerte par email ou autre

    # Lecture du dernier enregistrement de la table des données opérationnelles avec
    # l'horodateur et l'état de charge de la batterie
    curs.execute("select dtm, soc from onem order by dtm desc limit 1")
    onem_dtm, onem_soc = curs.fetchone()
    
    if genctrl == "AUTO":
        # Détermination du besoin de démarrage ou de l'arrêt de la génératrice
        resp = manage_gen(onem_soc, SOCmin, SOCmax, relay)
        
        current_state = getcurrentstate(relay)
        if current_state == "ERROR":
            relay_error_count += 1
            log.warning(f"Erreur de lecture du relais (compteur: {relay_error_count})")
        else:
            relay_error_count = 0  # Réinitialiser le compteur si succès
            
        log.debug(f"dtm={onem_dtm}, SOCmin={SOCmin}, SOC={onem_soc}, SOCmax={SOCmax}, resp = {resp}, currentstate={current_state}")

        # Contrôle du relais selon le besoin
        if resp == "ON": # Il faut démarrer la génératrice selon manage_gen()
            try:
                relay.state(1, on=True)
                log.debug("Generator AUTO ON")
            except Exception as e:
                log.error(f"Erreur lors de l'activation du relais: {e}")
                relay_error_count += 1
                
        if resp == "OFF": # Il faut arrêter la génératrice selon manage_gen()
            try:
                relay.state(1, on=False)
                log.debug("Generator auto off")
            except Exception as e:
                log.error(f"Erreur lors de la désactivation du relais: {e}")
                relay_error_count += 1

    elif genctrl == 'ON': # On force l'opération ON en mode manuel.
        log.debug('Generator MANUAL RUN')
        resp = "MANUAL"
        relay.state(1, on=True)

    elif genctrl == 'OFF': # On force l'opération OFF en mode manuel.
        log.debug('Generator MANUAL OFF')
        resp = "MANUAL"
        relay.state(1, on=False)

# Écriture de l'état dans un fichier texte pour communiquer l'état à d'autres programmes
    if ftype == 'txt':
        ftxt = "test.txt"
        with open(getconf('ftxt'), "w") as f:
            f.write(f"{onem_dtm},{SOCmin},{onem_soc},{SOCmax},{resp},{getcurrentstate(relay)}\n")
# Écriture de l'état dans une table SQLite3 seulement lors d'un changement de statut.
    if ftype == 'sql':
        if frun is None: # On lit les dernières valeurs au démarrage du programme
            log.debug("première run... On lit le dernier enregistrement de la table.")
            conn = sqlite3.connect(fSQLite)
            curs1 = conn.cursor()
            curs1.execute("SELECT * FROM magagss")
            seq, dtm, gencontrol, start_limit, soc, stop_limit, expected_state, relay_state = curs1.fetchone()
            conn.close()
            frun = 1

        conn = sqlite3.connect(fSQLite)
# Pour magags, on enregistre que si il y a un changement avec l'enregistrement précédent
        if gencontrol != genctrl or start_limit != SOCmin or stop_limit != SOCmax \
            or expected_state != resp or relay_state != getcurrentstate(relay):
            print(f"Différences dans les enregistrements... {onem_dtm}")
            conn.execute("""
            INSERT INTO magags VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, getcurrentstate(relay)))
            gencontrol = genctrl
            start_limit = SOCmin
            soc = onem_soc
            stop_limit = SOCmax
            expected_state = resp
            relay_state = getcurrentstate(relay)

# On conserve toujours le dernier état dans magagss dans un seul enregistrement
        conn.execute("""
        INSERT OR REPLACE INTO magagss VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, getcurrentstate(relay)))
        conn.commit()        
        conn.close()
        
        
# Gestion de la temporisation et sortie du programme
    duration = time.time() - start
    delay = interval - duration
    if delay > 0:
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            print("KeyboardInterrupt")
            cmd = 'STOP'
            conn.close()
            break

log.info("Fin de la boucle principale et du programme...")

conn.close()
