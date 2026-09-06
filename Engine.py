"""
Modified:
- Expose Pixi app through L2DNameSpace for external control
- Separate model scaling from visible viewer frame
- Add independent crop controls
"""

from browser import document, window, timer, bind
from typing import Mapping, Callable
from bake_logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# TAILLE UTILISEE POUR LE ZOOM DU MODELE
# ------------------------------------------------------------
#
# IMPORTANT :
# Ne pas modifier ces valeurs pour régler le crop.
# Elles donnent actuellement la bonne taille au modèle.
#

MODEL_AREA_WIDTH = 917
MODEL_AREA_HEIGHT = 788


# ------------------------------------------------------------
# TAILLE DU CADRE POINTILLE
# ------------------------------------------------------------

FRAME_WIDTH = 917
FRAME_HEIGHT = 788


# ------------------------------------------------------------
# CROP DU CONTENU
# ------------------------------------------------------------
#
# Ces valeurs permettent de masquer une partie du contenu
# à l'intérieur du cadre.
#
# Augmenter LEFT et RIGHT réduit la largeur visible.
# Augmenter TOP et BOTTOM réduit la hauteur visible.
#
# Exemple :
#
# CROP_LEFT = 20
# CROP_RIGHT = 20
#
# masque 20 pixels supplémentaires à gauche et à droite.
#

CROP_LEFT = 500
CROP_RIGHT = 500
CROP_TOP = 500
CROP_BOTTOM = 500


# ============================================================
# ELEMENTS HTML
# ============================================================

canvas_div = document["live2d_canvas"]
viewer_frame = document["viewer_frame"]


# ============================================================
# CONFIGURATION DU CADRE
# ============================================================

viewer_frame.style.position = "relative"
viewer_frame.style.width = f"{FRAME_WIDTH}px"
viewer_frame.style.height = f"{FRAME_HEIGHT}px"

viewer_frame.style.overflow = "hidden"
viewer_frame.style.boxSizing = "border-box"


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
# POSITIONNEMENT DU CANVAS
# ============================================================

def update_canvas_position():

    # --------------------------------------------------------
    # Le canvas reste de la taille du modèle.
    #
    # Le crop est obtenu en décalant le canvas derrière
    # le cadre visible.
    # --------------------------------------------------------

    crop_width = CROP_LEFT + CROP_RIGHT
    crop_height = CROP_TOP + CROP_BOTTOM


    visible_width = FRAME_WIDTH - crop_width
    visible_height = FRAME_HEIGHT - crop_height


    if visible_width <= 0:
        visible_width = 1

    if visible_height <= 0:
        visible_height = 1


    # --------------------------------------------------------
    # Décalage permettant de conserver le contenu centré.
    # --------------------------------------------------------

    offset_x = (FRAME_WIDTH - MODEL_AREA_WIDTH) / 2

    offset_y = (FRAME_HEIGHT - MODEL_AREA_HEIGHT) / 2


    # Le crop est appliqué symétriquement autour du centre.

    offset_x -= CROP_LEFT - CROP_RIGHT
    offset_y -= CROP_TOP - CROP_BOTTOM


    canvas_div.style.position = "absolute"

    canvas_div.style.left = f"{offset_x}px"
    canvas_div.style.top = f"{offset_y}px"


# Appliquer immédiatement le positionnement
update_canvas_position()


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
    # IMPORTANT :
    #
    # Le zoom du modèle reste exactement basé sur
    # MODEL_AREA_WIDTH / MODEL_AREA_HEIGHT.
    #
    # Le crop n'intervient absolument pas ici.
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
    # Centrage du modèle dans la zone de référence
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


    update_canvas_position()

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
