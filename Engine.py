"""Modified:
- Expose Pixi app through L2DNameSpace for external control
- Reproduce the centered Live2D visible viewport (837x727)
"""

from browser import document, window, timer, bind
from typing import Mapping, Callable
from bake_logger import logger


MODEL_SCALE_OFFSET = 0.85

canvas_div = document["live2d_canvas"]

pixi = window.PIXI
pixi.settings.RESOLUTION = window.devicePixelRatio

app = pixi.Application.new({
    "view": canvas_div,
    "transparent": True,
    "autoStart": True,
    "resizeTo": canvas_div
})


# ============================================================
# LIVE2D REFERENCE CANVAS
# ============================================================

# Original Live2D canvas
LIVE2D_WIDTH = 2000
LIVE2D_HEIGHT = 1775

# Visible area in Live2D
VIEW_WIDTH = 837
VIEW_HEIGHT = 727

# Center the visible area inside the original canvas
VIEW_X = (LIVE2D_WIDTH - VIEW_WIDTH) / 2
VIEW_Y = (LIVE2D_HEIGHT - VIEW_HEIGHT) / 2


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


def resize(model=None):

    if model is None:
        model = L2DNameSpace.current_model

    if not model:
        return

    # Size of the actual HTML canvas
    canvas_width = canvas_div.clientWidth
    canvas_height = canvas_div.clientHeight

    if canvas_width <= 0 or canvas_height <= 0:
        return

    # Calculate the scale needed to display
    # the 837x727 Live2D viewport.
    scale_x = canvas_width / VIEW_WIDTH
    scale_y = canvas_height / VIEW_HEIGHT

    camera_scale = min(scale_x, scale_y)

    # Zoom the entire Live2D canvas
    app.stage.scale.set(camera_scale)

    # Move the centered 837x727 viewport
    # into the visible HTML canvas.
    app.stage.x = -VIEW_X * camera_scale
    app.stage.y = -VIEW_Y * camera_scale

    logger.info(
        f"Resize camera_scale={camera_scale} "
        f"stage_pos={app.stage.x},{app.stage.y} "
        f"viewport={VIEW_WIDTH}x{VIEW_HEIGHT}"
    )


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


def on_window_resize():

    logger.debug("Pixi Resize triggered")

    app.resizeTo = canvas_div

    resize()


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


@bind(window, "resize")
def on_resize(*_):

    ResizeTimer.set_timer()
