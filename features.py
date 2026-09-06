"""
features.py

Viewer Interactive additional features

- blink
- Pants

"""

from browser import timer, window
import random


# ============================================================
# SETTINGS
# ============================================================

DEBUG_MODE = True

ENABLE_AUTO_BLINK = True
ENABLE_PANTS_TOUCH = True


BLINK_MIN_TIME = 3
BLINK_MAX_TIME = 7


# Zone pantalon relative au canvas
# A ajuster si nécessaire

PANTS_ZONE = {
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


    # Param4
    # -30 = closed
    # 30 = open

    set_parameter(
        "Param4",
        -30
    )


    timer.set_timeout(
        open_eyes,
        150
    )



def open_eyes():

    set_parameter(
        "Param4",
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
# PANTS
# ============================================================

pants_visible = True



def init_pants():

    global pants_visible


    pants_visible = True


    # Param7
    # -30 = ON
    # 30 = OFF

    set_parameter(
        "Param7",
        -30
    )


    debug("Pants ON")



def toggle_pants():

    global pants_visible


    if pants_visible:


        set_parameter(
            "Param7",
            30
        )


        pants_visible = False

        debug("Pants OFF")


    else:


        set_parameter(
            "Param7",
            -30
        )


        pants_visible = True

        debug("Pants ON")



# ============================================================
# TOUCH ZONE
# ============================================================

def check_pants_touch(event):

    if not ENABLE_PANTS_TOUCH:

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

        PANTS_ZONE["x"]
        <= nx
        <= PANTS_ZONE["x"] + PANTS_ZONE["width"]

        and

        PANTS_ZONE["y"]
        <= ny
        <= PANTS_ZONE["y"] + PANTS_ZONE["height"]

    ):


        debug("Pants zone touched")


        toggle_pants()



def enable_touch():

    if not ENABLE_PANTS_TOUCH:

        return


    try:


        canvas = window.document["live2d_canvas"]


        canvas.addEventListener(
            "pointerup",
            check_pants_touch
        )


        debug("Pointer touch enabled")



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



    init_pants()



    if ENABLE_AUTO_BLINK:


        schedule_blink()



    enable_touch()



    debug("Features loaded")



wait_for_model()
