module Menu.Types exposing (..)


type alias Model =
    { tiles : List Tile
    , id : String
    , lastKey : Char
    }


type alias Tile =
    { label : String
    , key : Char
    , x : Float
    , y : Float
    }


type Msg
    = KeyPress Int
    | NoOp


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
