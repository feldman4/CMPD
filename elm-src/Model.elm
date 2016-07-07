module Model exposing (..)

import Versus
import Menu.Types


type alias Model =
    { menu : Menu.Types.Model
    , loadout : Menu.Types.Model
    , encounter : Versus.Model
    , mapMenu : Menu.Types.Model
    , map : Map
    , overlay : Overlay
    , key : Int
    }


type Msg
    = UpdateMenu Menu.Types.Msg
    | UpdateLoadout Menu.Types.Msg
    | UpdateEncounter Versus.Msg
    | UpdateMapMenu Menu.Types.Msg
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
