"""
Modified:
- Expose Pixi app through L2DNameSpace for external control
- Separate model scaling from visible viewer frame
"""

from browser import document, window, timer, bind
from typing import Mapping, Callable
from bake_logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

# Taille de référence utilisée pour calculer le zoom du modèle.
#
# IMPORTANT :
# Ces valeurs correspondent à la taille qui donnait actuellement
# le bon zoom dans ton viewer.
#
# Elles ne correspondent PAS à la taille du cadre visible.
MODEL_AREA_WIDTH = 917
MODEL_AREA_HEIGHT = 788


# Taille de la fenêtre réellement visible.
#
# Le contenu qui dépasse cette zone sera simplement coupé.
VIEW_WIDTH = 837
VIEW_HEIGHT = 727


# ============================================================
# ELEMENTS HTML
# ============================================================

canvas_div = document["live2d_canvas"]
viewer_frame = document["viewer_frame"]


# ============================================================
# CONFIGURATION DU CADRE
# ============================================================

viewer_frame.style.width = f"{VIEW_WIDTH}px"
viewer_frame.style.height = f"{VIEW_HEIGHT}px"

viewer_frame.style.position = "relative"
viewer_frame.style.overflow = "hidden"


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
# RESIZE / MODEL SCALE
# ============================================================

def resize(model=None):

    if model is None:

        model = L2DNameSpace.current_model


    if not model:

        return


    # --------------------------------------------------------
    # IMPORTANT
    #
    # On NE regarde plus la taille du canvas HTML ici.
    #
    # Le zoom du modèle est toujours calculé avec :
    #
    #     917 × 788
    #
    # comme dans ton ancienne version fonctionnelle.
    # --------------------------------------------------------

    canvas_width = MODEL_AREA_WIDTH
    canvas_height = MODEL_AREA_HEIGHT


    model_width = model.width
    model_height = model.height


    scale_x = canvas_width / model_width
    scale_y = canvas_height / model_height


    scale = min(scale_x, scale_y)


    model.scale.set(scale)


    scaled_width = model.width
    scaled_height = model.height


    # --------------------------------------------------------
    # Centrage du modèle dans la zone de référence 917 × 788
    # --------------------------------------------------------

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
