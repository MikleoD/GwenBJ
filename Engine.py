"""
Modified:
- Expose Pixi app through L2DNameSpace for external control
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


class L2DNameSpace:
    """
    Namespace for debugging
    """

    last_source = None
    current_model = None
    last_hit_areas = None
    canvas_div = None

    # NEW
    # expose Pixi application
    app = None


window.L2DNameSpace = L2DNameSpace

# NEW
# make Pixi app accessible from javascript
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



    canvas_width = canvas_div.clientWidth

    canvas_height = canvas_div.clientHeight



    model_width = model.width

    model_height = model.height



    scale_x = canvas_width / model_width

    scale_y = canvas_height / model_height


    scale = min(scale_x, scale_y) * 0.90



    model.scale.set(scale)



    scaled_width = model.width

    scaled_height = model.height



    model.x = (canvas_width - scaled_width) / 2

    model.y = (canvas_height - scaled_height) / 2



    logger.info(
        f"Resize scale={scale} pos={model.x},{model.y}"
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
