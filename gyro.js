// ============================================================
// gyro.js
// Gyro -> Physics Body X
// ============================================================


(function(){


console.log("Gyro Physics Input loaded");


// Force du mouvement

const POWER = 7;


// vitesse oscillation

const SPEED = 24;


// seuil secousse

const LIMIT = 1.5;



let target = 0;

let current = 0;

let active = false;

let phase = 0;



// ------------------------------------------------------------
// Paramètre
// ------------------------------------------------------------

function setBodyX(value){


    try{


        let model =
            window.L2DNameSpace.current_model;


        if(!model){

            return;

        }


        model.internalModel.coreModel.setParameterValueById(

            "ParamBodyAngleX",

            value

        );


    }

    catch(e){

        console.log(e);

    }


}



// ------------------------------------------------------------
// Animation oscillation
// ------------------------------------------------------------

function update(){


    if(active){


        phase += 0.35;


        current =
            Math.sin(phase)
            *
            target;



        setBodyX(current);


    }

    else{


        current *= 0.85;


        setBodyX(current);



        if(Math.abs(current) < 0.1){

            current = 0;

            setBodyX(0);

        }


    }



    requestAnimationFrame(update);


}



update();



// ------------------------------------------------------------
// Détection mouvement téléphone
// ------------------------------------------------------------

function motion(event){


    let acc =
        event.accelerationIncludingGravity;



    if(!acc){

        return;

    }



    let x = acc.x || 0;

    let y = acc.y || 0;

    let z = acc.z || 0;



    let force =
        Math.sqrt(
            x*x +
            y*y +
            z*z
        );



    let movement =
        Math.abs(force - 9.8);



    if(movement > LIMIT){


        target =
            POWER;


        active = true;



        clearTimeout(
            window.gyroStop
        );


        window.gyroStop =
            setTimeout(

                function(){

                    active=false;

                },

                324

            );


    }


}



window.addEventListener(

    "devicemotion",

    motion,

    true

);



})();
