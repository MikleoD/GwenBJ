"""
features.py

Viewer Interactive additional features

- Auto blink
- Swimsuit toggle
"""

from browser import timer, window
import random


# ============================================================
# SETTINGS
# ============================================================

DEBUG_MODE = True

ENABLE_AUTO_BLINK = True
ENABLE_SWIMSUIT_TOUCH = True


BLINK_MIN_TIME = 3
BLINK_MAX_TIME = 7


# ============================================================
# SWIMSUIT TOUCH ZONE
# ============================================================
#
# Zone relative au canvas.
#
# x / y = position du coin supérieur gauche
# width / height = taille de la zone
#
# On garde pour l'instant la même zone que celle utilisée
# précédemment pour le pantalon de Lapis.
#

SWIMSUIT_ZONE = {
    "x": 0.30,
    "y": 0.45,
    "width": 0.40,
    "height": 0.35
}


# ============================================================
# CONNECTION
# ============================================================

try:

    from Engine import L2DNameSpace

except Exception:

    L2DNameSpace = None


def debug(text):

    if DEBUG_MODE:

        print("[Features]", text)


def get_model():

    if L2DNameSpace is None:

        return None


    return L2DNameSpace.current_model


# ============================================================
# PARAMETER CONTROL
# ============================================================

def set_parameter(parameter_id, value):

    model = get_model()


    if model is None:

        return


    try:

        model.internalModel.coreModel.setParameterValueById(
            parameter_id,
            value
        )


    except Exception as err:

        debug(
            "Parameter error "
            + parameter_id
            + " : "
            + str(err)
        )


# ============================================================
# BLINK
# ============================================================

def blink():

    debug("Blink")


    # BLINK
    # -30 = closed
    # 30 = open

    set_parameter(
        "BLINK",
        -30
    )


    timer.set_timeout(
        open_eyes,
        150
    )


def open_eyes():

    set_parameter(
        "BLINK",
        30
    )


def schedule_blink():

    if not ENABLE_AUTO_BLINK:

        return


    delay = random.uniform(
        BLINK_MIN_TIME,
        BLINK_MAX_TIME
    ) * 1000


    timer.set_timeout(
        lambda *_: (
            blink(),
            schedule_blink()
        ),
        delay
    )


# ============================================================
# SWIMSUIT
# ============================================================

swimsuit_visible = True


def init_swimsuit():

    global swimsuit_visible


    swimsuit_visible = True


    # SWIMSUIT
    # -30 = ON / visible
    # 30 = OFF / invisible

    set_parameter(
        "SWIMSUIT",
        -30
    )


    debug("Swimsuit ON")


def toggle_swimsuit():

    global swimsuit_visible


    if swimsuit_visible:

        set_parameter(
            "SWIMSUIT",
            30
        )


        swimsuit_visible = False

        debug("Swimsuit OFF")


    else:

        set_parameter(
            "SWIMSUIT",
            -30
        )


        swimsuit_visible = True

        debug("Swimsuit ON")


# ============================================================
# TOUCH ZONE
# ============================================================

def check_swimsuit_touch(event):

    if not ENABLE_SWIMSUIT_TOUCH:

        return


    canvas = window.document["live2d_canvas"]

    rect = canvas.getBoundingClientRect()


    # Pointer event fonctionne sur :
    # PC souris
    # Android tactile
    # iPhone tactile

    x = event.clientX - rect.left
    y = event.clientY - rect.top


    nx = x / rect.width
    ny = y / rect.height


    if (

        SWIMSUIT_ZONE["x"]
        <= nx
        <= SWIMSUIT_ZONE["x"] + SWIMSUIT_ZONE["width"]

        and

        SWIMSUIT_ZONE["y"]
        <= ny
        <= SWIMSUIT_ZONE["y"] + SWIMSUIT_ZONE["height"]

    ):

        debug("Swimsuit zone touched")

        toggle_swimsuit()


# ============================================================
# ENABLE TOUCH
# ============================================================

def enable_touch():

    if not ENABLE_SWIMSUIT_TOUCH:

        return


    try:

        canvas = window.document["live2d_canvas"]


        canvas.addEventListener(
            "pointerup",
            check_swimsuit_touch
        )


        debug("Swimsuit pointer touch enabled")


    except Exception as err:

        debug(
            "Touch error "
            + str(err)
        )


# ============================================================
# START
# ============================================================

def wait_for_model():

    model = get_model()


    if model is None:

        timer.set_timeout(
            wait_for_model,
            500
        )


        return


    debug("Model detected")


    init_swimsuit()


    if ENABLE_AUTO_BLINK:

        schedule_blink()


    enable_touch()


    debug("Features loaded")


wait_for_model()
