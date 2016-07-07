module Model exposing (..)

import Versus
import Menu exposing (Model)


type alias Model =
    { menu : Menu.Model
    , loadout : Menu.Model
    , encounter : Versus.Model
    , map : Map
    , overlay : Overlay
    , key : Int
    }


type Msg
    = UpdateMenu Menu.Msg
    | UpdateLoadout Menu.Msg
    | UpdateEncounter Versus.Msg
    | ChangeOverlay Overlay
    | KeyPress Int
    | SetMap Map
    | NoOp


type Overlay
    = NoOverlay
    | MenuOverlay
    | LoadoutOverlay
    | EncounterOverlay


type alias Map =
    { image : String, places : List Place }


type alias Place =
    { x : Float
    , y : Float
    , label : String
    }
