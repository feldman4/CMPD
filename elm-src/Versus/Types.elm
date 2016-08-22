module Versus.Types exposing (..)

import Bar
import Wordbank exposing (Word)
import Time


-- MODEL


type alias Model =
    { wordbank : Wordbank.Model
    , progressBar : Bar.Model
    , addInput : String
    , enemy : Enemy
    , player : Player
    , maxToDisplay : Int
    , conversation : List Remark
    , clock : Time.Time
    , firstTick : Bool
    , overload : Float
    , drainRate :
        Float
        -- 0.02 works
    }


type alias Remark =
    { insult : String
    , retort : String
    , score : Float
    }


type alias Player =
    { loaded : List Word
    , unloaded : List Word
    , capacity : List ( String, Int )
    , image : String
    , name : String
    , health : Float
    }


type alias Enemy =
    { image : String
    , name : String
    , health : Float
    }



-- UPDATE


type Msg
    = NoOp
    | NewWordbank (List Word)
    | UpdateWordbank Wordbank.Msg
    | UpdateAddInput String
    | AskSuggestions String
    | Suggest (List String)
    | EnterInput
    | AddRemark Remark
    | SetEnemy Enemy
    | SetEnemyImage String
    | UpdateProgressBar Bar.Msg
    | Tick Time.Time
