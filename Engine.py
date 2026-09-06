"""
Modified:
- Expose Pixi app through L2DNameSpace for external control
- Separate original canvas size from visible viewer frame
- Keep Live2D model centered inside the original canvas
- Viewer frame acts only as a clipping window
"""

from browser import document, window, timer, bind
from typing import Mapping, Callable
from bake_logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

# Taille originale du canvas du fanart dans Live2D
ORIGINAL_WIDTH = 2000
ORIGINAL_HEIGHT = 1775

# Taille de la partie que l'on veut voir dans le viewer
VIEW_WIDTH = 917
VIEW_HEIGHT = 788


# ============================================================
# ELEMENTS HTML
# ============================================================

canvas_div = document["live2d_canvas"]
viewer_frame = document["viewer_frame"]


# ============================================================
# CONFIGURATION DU CANVAS
# ============================================================

# Le canvas conserve la taille originale du fanart.
#
# Le cadre visible sera plus petit et servira simplement
# de fenêtre de découpe.

canvas_div.style.width = f"{ORIGINAL_WIDTH}px"
canvas_div.style.height = f"{ORIGINAL_HEIGHT}px"

viewer_frame.style.width = f"{VIEW_WIDTH}px"
viewer_frame.style.height = f"{VIEW_HEIGHT}px"


# Le canvas est placé au centre du cadre.
#
# Comme le canvas est plus grand que le cadre, une partie
# du canvas dépasse de chaque côté et est masquée par
# overflow:hidden.

canvas_div.style.position = "absolute"

canvas_div.style.left = f"{(VIEW_WIDTH - ORIGINAL_WIDTH) / 2}px"
canvas_div.style.top = f"{(VIEW_HEIGHT - ORIGINAL_HEIGHT) / 2}px"


# ============================================================
# PIXI
# ============================================================

pixi = window.PIXI


pixi.settings.RESOLUTION = window.devicePixelRatio


app = pixi.Application.new({
    "view": canvas_div,
    "transparent": True,
    "autoStart": True,
    "resizeTo": canvas_div
})


# ============================================================
# LIVE2D NAMESPACE
# ============================================================

class L2DNameSpace:
    """
    Namespace for debugging
    """

    last_source = None
    current_model = None
    last_hit_areas = None
    canvas_div = None

    # Expose Pixi application
    app = None


window.L2DNameSpace = L2DNameSpace


# Make Pixi app accessible from JavaScript
L2DNameSpace.app = app


# ============================================================
# LOAD LIVE2D
# ============================================================

def load_live2d(json_or_url: Mapping | str, callback: Callable):

    if not json_or_url:
        raise ValueError("No url is provided")


    logger.debug(f"Loading {json_or_url}")


    L2DNameSpace.last_source = json_or_url


    if L2DNameSpace.current_model is not None:

        try:

            app.stage.removeChildAt(0)

            L2DNameSpace.current_model = None


        except Exception as err:

            logger.critical(err)


        else:

            logger.info("Unloaded previous model")


    logger.info("Loading new model")


    model = pixi.live2d.Live2DModel.fromSync(json_or_url)


    model.once(
        "load",
        lambda *_: model_load_callback(model, callback)
    )


# ============================================================
# MODEL LOAD CALLBACK
# ============================================================

def model_load_callback(model, callback):

    logger.debug("in callback")


    L2DNameSpace.current_model = model


    try:

        app.stage.addChild(model)


        model.on(
            "hit",
            model_hit_callback_closure(model)
        )


        resize(model)


    finally:

        callback()


# ============================================================
# RESIZE / CENTERING
# ============================================================

def resize(model=None):

    if model is None:

        model = L2DNameSpace.current_model


    if not model:

        return


    # IMPORTANT :
    # Le modèle est maintenant dimensionné par rapport
    # au canvas ORIGINAL, et non par rapport au cadre visible.

    canvas_width = ORIGINAL_WIDTH
    canvas_height = ORIGINAL_HEIGHT


    model_width = model.width
    model_height = model.height


    scale_x = canvas_width / model_width
    scale_y = canvas_height / model_height


    scale = min(scale_x, scale_y)


    model.scale.set(scale)


    scaled_width = model.width
    scaled_height = model.height


    # Centrage dans le canvas original

    model.x = (canvas_width - scaled_width) / 2
    model.y = (canvas_height - scaled_height) / 2


    logger.info(
        f"Resize scale={scale} pos={model.x},{model.y}"
    )


# ============================================================
# HIT CALLBACK
# ============================================================

def model_hit_callback_closure(model):

    def model_hit_callback(hit_areas):

        L2DNameSpace.last_hit_areas = hit_areas


        logger.info(
            f"Touch on {hit_areas}"
        )


        for hit_area in hit_areas:

            match hit_area:

                case "body":

                    model.motion("tap_body")


                case "Body":

                    model.motion("Tap")


                case "head" | "Head":

                    model.expression()


                case _:

                    logger.debug(
                        f"Unregistered hit area {hit_area}, ignoring"
                    )


    return model_hit_callback


# ============================================================
# WINDOW RESIZE
# ============================================================

def on_window_resize():

    logger.debug("Pixi Resize triggered")


    app.resizeTo = canvas_div


    resize()


# ============================================================
# RESIZE TIMER
# ============================================================

class ResizeTimer:

    active_timer = None

    refresh_delay = 300


    @classmethod
    def set_timer(cls):

        if cls.active_timer is not None:

            timer.clear_timeout(cls.active_timer)


        cls.active_timer = timer.set_timeout(
            on_window_resize,
            cls.refresh_delay
        )


# ============================================================
# BROWSER RESIZE
# ============================================================

@bind(window, "resize")
def on_resize(*_):

    ResizeTimer.set_timer()
