module Map.Types exposing (..)

import Menu.Types


type alias Model =
    { map : Map
    , menu : Menu.Types.Model
    }


type Msg
    = UpdateMenu Menu.Types.Msg



type alias Map =
    { image : String, name: String, places : List Place }



type alias Place =
    { x : Float
    , y : Float
    , label : String
    , key : String
    }

