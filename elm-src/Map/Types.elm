module Map.Types exposing (..)

import Versus
import Menu.Types
import Loadout.Loadout


type alias Model =
    { menu : Menu.Types.Model
    , loadout : Loadout.Loadout.Model
    , weapons : Menu.Types.Model
    , encounter : Versus.Model
    , mapMenu : Menu.Types.Model
    , map : Map
    , overlay : Overlay
    , key : Int
    , player : Player
    }


type Msg
    = UpdateMenu Menu.Types.Msg
    | UpdateLoadout Loadout.Loadout.Msg
    | UpdateWeapons Menu.Types.Msg
    | UpdateEncounter Versus.Msg
    | UpdateMapMenu Menu.Types.Msg
    | ChangeOverlay Overlay
    | KeyPress Int
    | SetMap Map
    | SetPlayer Player
    | NoOp


type Overlay
    = NoOverlay
    | MenuOverlay
    | LoadoutOverlay
    | EncounterOverlay Char
    | WeaponsOverlay


type alias Player =
    { loaded : List Word
    , unloaded : List Word
    , capacity : List ( String, Int )
    }


type alias Map =
    { image : String, places : List Place }


type alias Word =
    { word : String
    , partOfSpeech : String
    }


type alias Place =
    { x : Float
    , y : Float
    , label : String
    , enemy : String
    }
