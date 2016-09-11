port module Versus.Versus exposing (..)

import Bar
import Versus.Types exposing (..)
import Versus.View exposing (view, viewMain)
import Wordbank exposing (Word)
import Html exposing (Html, button, div, text, img, input, Attribute)
import Html.App as App
import Html.Events exposing (onClick, onInput, keyCode, on)
import Json.Decode as Json
import Time
import AnimationFrame


main : Program Never
main =
    let
        words =
            []

        player =
            { capacity = [], loaded = [], unloaded = [], image = "", name = "player", health = 1 }

        enemy =
            { image = "", name = "enemy", health = 1 }

        maxToDisplay =
            30
    in
        App.program
            { init = init (testWords1 ++ testWords2) testPlayer testEnemy maxToDisplay
            , update = update
            , view = viewMain
            , subscriptions = subscriptions
            }


init : List Word -> Player -> Enemy -> Int -> ( Model, Cmd Msg )
init words player enemy maxToDisplay =
    let
        model =
            { wordbank = Wordbank.init [] 0
            , progressBar = Bar.init 0.5 True
            , enemy = enemy
            , player = player
            , maxToDisplay = maxToDisplay
            , addInput = ""
            , conversation = []
            , clock = 0
            , firstTick = True
            , overload = 0.833
            , drainRate = 0
            }
    in
        update (NewWordbank words) model


inputID : String
inputID =
    "#input-input"



-- TEST


testPlayer : Player
testPlayer =
    { loaded = testWords1
    , unloaded = testWords2
    , capacity = testCapacity
    , health = 1
    , image = "http://cdn.cnsnews.com/itfoe-reagan.png"
    , name = "player"
    }


testWords1 : List { partOfSpeech : String, tag : String, word : String }
testWords1 =
    [ { word = "Test", partOfSpeech = "1", tag = "whatevs" }
    , { word = "Another Test", partOfSpeech = "1", tag = "asdf" }
    , { word = "ABC", partOfSpeech = "2", tag = "alphabet" }
    ]


testWords2 : List { partOfSpeech : String, tag : String, word : String }
testWords2 =
    [ { word = "Unloaded", partOfSpeech = "2", tag = "asdf" } ]


testCapacity : List ( String, number )
testCapacity =
    [ ( "2", 2 ), ( "1", 1 ) ]


testEnemy : Enemy
testEnemy =
    { image = "http://cdn1.askiitians.com/cms-content/biologyanimal-kingdomphylum-ctenophora-aschelminthes-and-platyhelminthes_1.jpg", name = "test", health = 1 }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update message model =
    case message of
        NoOp ->
            model ! []

        NewWordbank words ->
            { model | wordbank = Wordbank.init words model.maxToDisplay } ! []

        UpdateWordbank msg ->
            { model
                | wordbank = Wordbank.update msg model.wordbank
            }
                ! []

        UpdateProgressBar msg ->
            { model
                | progressBar = Bar.update msg model.progressBar
            }
                ! []

        UpdateAddInput input ->
            update (AskSuggestions input) { model | addInput = input }

        AskSuggestions word ->
            ( model, askFuse ( word, List.map (\( w, visible ) -> w.word) model.wordbank.words ) )

        Suggest suggestions ->
            let
                wordbankWords =
                    model.wordbank.words

                suggestionWords =
                    List.filter (\( w, visible ) -> List.member w.word suggestions) wordbankWords
                        |> List.map (\( w, visible ) -> w)
            in
                { model
                    | wordbank =
                        Wordbank.update (Wordbank.ShowWords suggestionWords)
                            model.wordbank
                }
                    ! []

        EnterInput ->
            let
                maybe =
                    List.head
                        (List.map fst
                            (List.filter (\( w, b ) -> b) model.wordbank.words)
                        )
            in
                case maybe of
                    Just word ->
                        ( { model | addInput = "" }, sendInsult ( word, model.progressBar.value ) )

                    Nothing ->
                        model ! []

        AddRemark remark ->
            let
                progress =
                    max (min remark.health 1) 0
            in
                ( { model
                    | conversation = model.conversation ++ [ remark ]
                    , progressBar = Bar.update (Bar.ChangeValue progress) model.progressBar
                  }
                , scrollTop "#output"
                )

        SetEnemy enemy ->
            { model | enemy = enemy } ! []

        SetEnemyImage image ->
            let
                enemy =
                    model.enemy

                newEnemy =
                    { enemy | image = image }
            in
                { model | enemy = newEnemy } ! []

        Tick newTime ->
            let
                elapsed =
                    if model.firstTick then
                        0
                    else
                        Time.inSeconds (newTime - model.clock)

                progress =
                    max (model.progressBar.value - model.drainRate * elapsed) 0

                progressBar =
                    Bar.update (Bar.ChangeValue progress) model.progressBar

                progressBar2 =
                    { progressBar
                        | sliderClasses =
                            if progress > model.overload then
                                [ "overload" ]
                            else
                                [ "normal" ]
                    }
            in
                { model
                    | clock = newTime
                    , progressBar = progressBar2
                    , firstTick = False
                }
                    ! []


showWordbankWord : Word -> Wordbank.Model -> Wordbank.Model
showWordbankWord word model =
    Wordbank.update (Wordbank.Show word) model


onEnter : Msg -> Attribute Msg
onEnter msg =
    let
        tagger code =
            if code == 13 then
                msg
            else
                NoOp
    in
        on "keydown" (Json.map tagger keyCode)



-- OUTGOING


port askFuse : ( String, List String ) -> Cmd msg


port sendInsult : ( Word, Float ) -> Cmd msg


port scrollTop : String -> Cmd msg



-- SUBSCRIPTIONS


port setWordbank : (List Word -> msg) -> Sub msg


port suggestions : (List String -> msg) -> Sub msg


port addRemark : (Remark -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ suggestions Suggest
        , setWordbank NewWordbank
        , addRemark AddRemark
        , AnimationFrame.times Tick
        ]
