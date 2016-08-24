module Game.Types exposing (..)

import Message.Message as Message exposing (Message)
import Versus.Types exposing (Player, Enemy)
import Menu.Types
import Map.Types exposing (Map)
import Loadout.Loadout as Loadout
import Char


type alias Model =
    { menu : Menu.Types.Model
    , loadout : Loadout.Model
    , versus : Versus.Types.Model
    , map : Map.Types.Model
    , message : Message.Model
    , loadoutStatus : OverlayStatus
    , menuStatus : OverlayStatus
    , mapStatus : OverlayStatus
    , versusStatus : OverlayStatus
    , messageStatus : OverlayStatus
    , player : Player
    }


type Msg
    = UpdateVersus Versus.Types.Msg
    | UpdateLoadout Loadout.Msg
    | UpdateMenu Menu.Types.Msg
    | UpdateMap Map.Types.Msg
    | UpdateMessage Message.Msg
    | SetMap Map
    | SetPlayer Player
    | SetVersus Enemy
    | SetMessage Message
    | KeyPress Char.KeyCode
    | NoOp


type alias Place =
    { x : Float
    , y : Float
    , label : String
    , key : Char
    , preview : String
    }


type alias Place_ =
    { x : Float
    , y : Float
    , label : String
    , key : String
    , preview : String
    }


type OverlayStatus
    = Active
    | Inactive
    | Hidden
