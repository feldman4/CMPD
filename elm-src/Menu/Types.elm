module Menu.Types exposing (..)


type alias Model =
    { tiles : List Tile
    , id : String
    , lastKey : Int
    , active : Bool
    }


type alias Tile =
    { label : String
    , key : Char
    , id : String
    , x : Float
    , y : Float
    }


type Msg
    = KeyPress Int
    | Activate Bool
    | NoOp