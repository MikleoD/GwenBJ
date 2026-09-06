"""
# Main script
# Modified for Personal Settings
"""


from browser import document, aio, window, bind, html

from bake_logger import logger
from Engine import load_live2d, L2DNameSpace


LAPIS_MODEL_URL = r"https://mikleod.github.io/LaLaBB/legacy_js_ver/A01.model3.json"


@bind(document["input_btn"], "click")
def on_click(*_):

    text_val = document["input_field"].value


    if text_val:

        logger.info(f"Loading {text_val}")


    else:

        logger.info("No url provided - loading Lapis")

        text_val = LAPIS_MODEL_URL

        document["input_field"].value = text_val



    button = document["input_btn"]

    button.attrs["disabled"] = ''



    load_live2d(
        text_val,
        callback_load
    )





@bind(document["interaction_check"], "click")
def on_interaction_check(*_):

    logger.info("Interaction changed")


    if L2DNameSpace.current_model is None:

        return


    L2DNameSpace.current_model.interactive = document["interaction_check"].checked





def list_emotion():

    logger.info("Checking motion/emotion entries")


    model = L2DNameSpace.current_model


    motions = list(
        model.internalModel.motionManager.definitions.to_dict().keys()
    )


    try:

        emotions = [
            obj.Name
            for obj in model.internalModel.motionManager.expressionManager.definitions
        ]


    except AttributeError:

        emotions = [
            obj.name
            for obj in model.internalModel.motionManager.expressionManager.definitions
        ]



    motion_div = document["motion_list"]

    emotion_div = document["emotion_list"]


    motion_div.replaceChildren()

    emotion_div.replaceChildren()



    for entry in motions:

        assert motion_div <= html.P(

            html.LABEL(

                html.INPUT(
                    type="checkbox",
                    id=f"motion_{entry}"
                )

                + entry

            ),

            Class="Entry"

        )



    for entry in emotions:

        assert emotion_div <= html.P(

            html.LABEL(

                html.INPUT(
                    type="checkbox",
                    id=f"emote_{entry}"
                )

                + entry

            ),

            Class="Entry"

        )





def callback_load():

    logger.info("Loading done")
    logger.info("MODEL LOADED SUCCESSFULLY")

    window.L2DNameSpace = L2DNameSpace

    try:

        del document["input_btn"].attrs["disabled"]


    except Exception:

        pass



    try:

        list_emotion()


    except Exception as err:

        logger.critical(f"{repr(err)}")







def on_load():


    header = document["header"]

    header.innerHTML = "Lapis-lazuli Live2D"



    # Redirect console

    window.console_redirect_init()



    logger.info("Automatic loading Lapis")



    

    document["input_field"].value = LAPIS_MODEL_URL




    on_click()





on_load()
