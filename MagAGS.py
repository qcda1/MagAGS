#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Programme de suivi de l'état de charge SOC de la batterie et contrôle
# de la génératrice selon des seuils minimum et maximum.
# Ce programme a été fait pour remplacer le module ME-BMK de Magnum-Energy
# qui a des problèmes à effectuer le suivi du SOC de la batterie.
#
# Auteur: Daniel Cote, Mars 2025
# Migré vers YAML pour la configuration.
#

import logging
import sqlite3
import time
import yaml
from datetime import date, datetime
from relay import Relay
from manage_gen import manage_gen

# ===========Chargement de la configuration==========================================

def load_config(path: str = "MagAGS.yaml") -> dict:
    """Charge et retourne le fichier de configuration YAML."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Chargement initial de la configuration
conf = load_config()

# ===========Utilitaires=============================================================

def llevel(level: str) -> int:
    """Convertit les niveaux de sévérité en leur valeur entière.
    Retourne 20 (INFO) par défaut si aucun match.
    """
    levels = {
        'DEBUG':    10,
        'INFO':     20,
        'WARNING':  30,
        'ERROR':    40,
        'CRITICAL': 50,
    }
    return levels.get(level, 20)


def reload_config(path: str = "MagAGS.yaml") -> dict:
    """Recharge le fichier de configuration à chaque itération de la boucle.
    Permet de modifier la configuration sans redémarrer le programme.
    """
    try:
        return load_config(path)
    except Exception as e:
        log.error(f"Erreur lors du rechargement de la configuration: {e}")
        return conf  # Retourne l'ancienne configuration en cas d'erreur


def is_time2exercise(t: str, duration: int = 1200) -> bool:
    """Détermine si c'est le moment de faire l'exercice de la génératrice.

    L'exercice a lieu le premier dimanche du mois, à l'heure t,
    pour une durée de `duration` secondes.

    Args:
        t:        Heure cible au format 'HHMM'.
        duration: Fenêtre de temps en secondes pendant laquelle la condition est vraie.

    Returns:
        True si les trois conditions sont réunies, False sinon.
    """
    log.debug(f"Entrée dans is_time2exercise: t={t}, duration={duration}")

    # --- Validation du format 'HHMM' ---
    if len(t) != 4 or not t.isdigit():
        log.error(f"Format de l'heure incorrect: {t}")
        return False
    hh, mm = int(t[:2]), int(t[2:])
    if hh > 23 or mm > 59:
        log.error(f"Heure incorrecte: {hh}:{mm}")
        return False

    today = date.today()
    now = datetime.now()

    # --- Condition 1 : premier dimanche du mois ---
    log.debug(f"Sommes-nous le premier dimanche du mois: {today.weekday()} == 6 and {today.day} <= 7")
    if not (today.weekday() == 6 and today.day <= 7):
        return False

    # --- Condition 2 : l'heure t est atteinte ---
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    log.debug(f"Heure {now} avant {target}")
    if now < target:
        return False

    # --- Condition 3 : moins de `duration` secondes depuis t ---
    elapsed = (now - target).total_seconds()
    log.debug(f"Temps écoulé: {elapsed} secondes")
    return elapsed < duration


def getcurrentstate(relay) -> str:
    """Lit l'état courant du relais avec 3 tentatives.

    Returns:
        'ON', 'OFF', ou 'ERROR'.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return 'ON' if relay.state(1) is True else 'OFF'
        except Exception as e:
            log.error(f"Erreur lors de la lecture de l'état du relais "
                      f"(tentative {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    return "ERROR"


def reconnect_relay(relay, max_attempts: int = 3, delay: int = 2):
    """Tente de reconnecter le relais en fermant proprement l'ancienne connexion
    et en créant une nouvelle — équivalent à un arrêt/redémarrage du programme.

    Args:
        relay:        Objet Relay existant (peut être None).
        max_attempts: Nombre de tentatives de reconnexion.
        delay:        Délai en secondes entre les tentatives.

    Returns:
        Nouvel objet Relay si succès, None sinon.
    """
    for attempt in range(max_attempts):
        try:
            log.warning(f"Tentative de reconnexion au relais ({attempt + 1}/{max_attempts})")

            # Fermer proprement l'ancienne connexion
            try:
                if relay is not None:
                    relay.close()
                    log.debug("Ancienne connexion au relais fermée")
            except Exception as e:
                log.debug(f"Erreur lors de la fermeture (ignorée): {e}")

            time.sleep(delay)

            # Créer une nouvelle connexion
            new_relay = Relay(idVendor=0x16c0, idProduct=0x05df)
            new_relay.state(0, on=False)
            new_relay.state(1)  # Lecture de test

            log.info("Relais reconnecté avec succès")
            return new_relay

        except Exception as e:
            log.error(f"Échec de reconnexion (tentative {attempt + 1}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)

    log.critical("Toutes les tentatives de reconnexion ont échoué")
    return None


# ===========Programme Principal=====================================================

# Configuration du logging
fmt = '%(asctime)s %(levelname)s %(lineno)s %(message)s'
logging.basicConfig(
    level=llevel(conf['logging']['level']),
    filename=conf['logging']['file'],
    format=fmt
)
log = logging.getLogger('MagAGS')

log.info("Début du programme")
log.info(f"Log level= {conf['logging']['level']}")

# Sauvegarde du niveau de log pour détecter les changements
loglb = conf['logging']['level']

# Intervalle de temps de la boucle principale (secondes)
interval = 60

# Condition de la boucle sans fin
cmd = 'RUN'

# Mémorise l'état précédent pour la table magagss (évite les écritures inutiles)
frun = None
gencontrol_prev = start_limit_prev = stop_limit_prev = expected_state_prev = relay_state_prev = None

# Réponse de manage_gen() : 'ON', 'OFF', ou 'MANUAL'
resp = ''

# Connexion à la base de données opérationnelle (lecture du SOC)
conn = sqlite3.connect("/usr/local/bin/monitormidnite/monitormidnite.db")
curs = conn.cursor()

# Initialisation du relais
relay = Relay(idVendor=0x16c0, idProduct=0x05df)
relay.state(0, on=False)  # Tous les canaux à OFF au démarrage

relay_error_count = 0
max_relay_errors  = 5     # Reconnecter après 5 erreurs consécutives

exercise_gen = False      # True si la génératrice est en période d'exercice


# ===========Boucle principale=======================================================

while cmd == 'RUN':
    start = time.time()
    log.debug("\nDébut de la boucle principale... %s", time.ctime())

    # --- Rechargement de la configuration à chaque itération ---
    conf = reload_config()

    # Détection d'un changement de niveau de log
    logl = conf['logging']['level']
    log.setLevel(llevel(logl))
    if logl != loglb:
        log.info(f"Changement de log level de {loglb} à {logl}")
        loglb = logl

    # Contrôle de l'exécution du programme
    cmd = conf['cmd']

    # --- Exercice de la génératrice ---
    # Démarrage chaque premier dimanche du mois à exercise.time pour exercise.duration secondes.
    exercise_enabled  = conf['generator']['exercise']['enabled']
    exercise_time     = conf['generator']['exercise']['time']
    exercise_duration = conf['generator']['exercise']['duration']

    log.debug(f"exercise_enabled={exercise_enabled}, exercise_time={exercise_time}, "
              f"exercise_duration={exercise_duration}")

    if exercise_enabled and is_time2exercise(exercise_time, exercise_duration):
        log.debug(f"Nous sommes le premier dimanche du mois et il est passé {exercise_time}, exercise_gen={exercise_gen}")
        if not exercise_gen:
            relay.state(1, on=True)
            log.info("Période d'exercice activée...")
            exercise_gen = True
    else:
        if exercise_gen:
            relay.state(1, on=False)
            log.info("Période d'exercice terminée...")
            exercise_gen = False

        log.debug(f"Hors période d'exercice: exercise_enabled={exercise_enabled}, "
                  f"exercise_gen={exercise_gen}")

        # --- Contrôle selon le SOC ---
        SOCmin  = conf['generator']['soc_min']
        SOCmax  = conf['generator']['soc_max']
        genctrl = conf['generator']['control']
        ftype   = conf['output']['type']
        ftxt    = conf['output']['txt_file']
        fSQLite = conf['output']['sqlite_file']

        # Reconnexion du relais si trop d'erreurs consécutives
        if relay_error_count >= max_relay_errors:
            log.warning("Trop d'erreurs de relais détectées, tentative de reconnexion complète...")
            new_relay = reconnect_relay(relay, max_attempts=3, delay=3)
            if new_relay is not None:
                relay = new_relay
                relay_error_count = 0
                log.info("Relais reconnecté — reprise normale des opérations")
            else:
                log.critical("Impossible de reconnecter le relais après plusieurs tentatives")
                # Option: envoyer une alerte par email ou autre

        # Lecture du dernier enregistrement de la table des données opérationnelles avec
        # l'horodateur (UTC) et l'état de charge de la batterie
        curs.execute("SELECT dtm, soc FROM onem ORDER BY dtm DESC LIMIT 1")
        onem_dtm, onem_soc = curs.fetchone()

        if genctrl == "AUTO":
            resp = manage_gen(onem_soc, SOCmin, SOCmax, relay)

            current_state = getcurrentstate(relay)
            if current_state == "ERROR":
                relay_error_count += 1
                log.warning(f"Erreur de lecture du relais (compteur: {relay_error_count})")
            else:
                relay_error_count = 0

            log.debug(f"dtm={onem_dtm} (UTC), SOCmin={SOCmin}, SOC={onem_soc}, "
                      f"SOCmax={SOCmax}, resp={resp}, currentstate={current_state}")

            if resp == "ON":
                try:
                    relay.state(1, on=True)
                    log.debug(f"Génératrice ON — genctrl={genctrl} relay={getcurrentstate(relay)}")
                except Exception as e:
                    log.error(f"Erreur lors de l'activation du relais: {e}")
                    relay_error_count += 1

            elif resp == "OFF":
                try:
                    relay.state(1, on=False)
                    log.debug(f"Génératrice OFF — genctrl={genctrl} relay={getcurrentstate(relay)}")
                except Exception as e:
                    log.error(f"Erreur lors de la désactivation du relais: {e}")
                    relay_error_count += 1

        elif genctrl == 'ON':
            log.debug(f"Mode MANUEL ON — relay={getcurrentstate(relay)}")
            resp = "MANUAL"
            relay.state(1, on=True)

        elif genctrl == 'OFF':
            log.debug(f"Mode MANUEL OFF — relay={getcurrentstate(relay)}")
            resp = "MANUAL"
            relay.state(1, on=False)

    # --- Écriture de l'état ---

    if ftype == 'txt':
        with open(ftxt, "w") as f:
            f.write(f"{onem_dtm},{SOCmin},{onem_soc},{SOCmax},{resp},{getcurrentstate(relay)}\n")

    if ftype == 'sql':
        current_state = getcurrentstate(relay)

        # Lecture du dernier enregistrement au premier démarrage
        if frun is None:
            log.debug("Première itération — lecture du dernier enregistrement de magagss.")
            db = sqlite3.connect(fSQLite)
            cur1 = db.cursor()
            cur1.execute("SELECT * FROM magagss")
            row = cur1.fetchone()
            db.close()
            if row:
                _, _, gencontrol_prev, start_limit_prev, _, stop_limit_prev, \
                    expected_state_prev, relay_state_prev = row
            frun = 1

        db = sqlite3.connect(fSQLite)

        # Enregistrement dans magags seulement en cas de changement
        if (gencontrol_prev != genctrl or start_limit_prev != SOCmin
                or stop_limit_prev != SOCmax or expected_state_prev != resp
                or relay_state_prev != current_state):
            log.warning(f"Changement détecté — enregistrement dans magags: {onem_dtm}")
            db.execute(
                "INSERT INTO magags VALUES (?, ?, ?, ?, ?, ?, ?)",
                (onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, current_state)
            )
            gencontrol_prev   = genctrl
            start_limit_prev  = SOCmin
            stop_limit_prev   = SOCmax
            expected_state_prev = resp
            relay_state_prev  = current_state

        # Toujours conserver le dernier état dans magagss (un seul enregistrement)
        db.execute(
            "INSERT OR REPLACE INTO magagss VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, current_state)
        )
        db.commit()
        db.close()

    # --- Gestion de la temporisation et sortie du programme ---

    if cmd != 'RUN':
        log.info(f"cmd != 'RUN', sortie de la boucle principale: {cmd}")
        conn.close()
        break

    duration = time.time() - start
    delay = interval - duration
    if delay > 0:
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            print("KeyboardInterrupt")
            conn.close()
            break

log.info("Fin de la boucle principale et du programme...")
conn.close()
