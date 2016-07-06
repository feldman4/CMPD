module Model exposing (..)

import Versus
import Menu exposing (Model)


type alias Model =
    { menu : Menu.Model
    , loadout : Menu.Model
    , encounter : Versus.Model
    , image : String
    , overlay : Overlay
    , key : Int
    }


type Msg
    = UpdateMenu Menu.Msg
    | UpdateLoadout Menu.Msg
    | UpdateEncounter Versus.Msg
    | ChangeOverlay Overlay
    | KeyPress Int
    | SetMapImage String
    | NoOp


type Overlay
    = NoOverlay
    | MenuOverlay
    | LoadoutOverlay
    | EncounterOverlay
