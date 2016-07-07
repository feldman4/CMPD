port module Versus exposing (..)

import Bar
import Wordbank
import Html exposing (Html, button, div, text, img, input, Attribute)
import Html.Attributes exposing (value, placeholder, id, src, class, autofocus, itemprop)
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

        enemyImage =
            ""

        maxToDisplay =
            30
    in
        App.program
            { init = init words enemyImage maxToDisplay
            , update = update
            , view = view
            , subscriptions = subscriptions
            }



-- MODEL


type alias Model =
    { wordbank : Wordbank.Model
    , progressBar : Bar.Model
    , addInput : String
    , enemyImage : String
    , maxToDisplay : Int
    , conversation : List Remark
    , clock : Time.Time
    , firstTick : Bool
    , overload : Float
    }


init : List String -> String -> Int -> ( Model, Cmd Msg )
init words enemyImage maxToDisplay =
    let
        model =
            { wordbank = Wordbank.init [] 0
            , progressBar = Bar.init 0.5 True
            , enemyImage = enemyImage
            , maxToDisplay = maxToDisplay
            , addInput = ""
            , conversation = []
            , clock = 0
            , firstTick = True
            , overload = 0.833
            }
    in
        update (NewWordbank words) model


type alias Remark =
    { insult : String
    , retort : String
    , score : Float
    }


inputID : String
inputID =
    "#input-input"



-- UPDATE


type Msg
    = NoOp
    | NewWordbank (List String)
    | UpdateWordbank Wordbank.Msg
    | UpdateAddInput String
    | AskSuggestions String
    | Suggest (List String)
    | EnterInput
    | AddRemark Remark
    | SetEnemyImage String
    | UpdateProgressBar Bar.Msg
    | Tick Time.Time


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
            ( model, askFuse ( word, List.map fst model.wordbank.words ) )

        Suggest suggestions ->
            { model
                | wordbank =
                    Wordbank.update (Wordbank.ShowWords suggestions)
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
                    max (min (model.progressBar.value + remark.score) 1) 0
            in
                ( { model
                    | conversation = model.conversation ++ [ remark ]
                    , progressBar = Bar.update (Bar.Value progress) model.progressBar
                  }
                , scrollTop "#output"
                )

        SetEnemyImage src ->
            { model | enemyImage = src } ! []

        Tick newTime ->
            let
                elapsed =
                    if model.firstTick then
                        0
                    else
                        Time.inSeconds (newTime - model.clock)

                progress =
                    max (model.progressBar.value - 0.02 * elapsed) 0

                progressBar =
                    Bar.update (Bar.Value progress) model.progressBar

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


showWordbankWord : String -> Wordbank.Model -> Wordbank.Model
showWordbankWord word model =
    Wordbank.update (Wordbank.Show word) model



-- VIEW
-- the following tags the Html Msg bag coming out of model.wordbank with
-- the new type TheWordbank so it can be matched and processed by
-- this model's update function. confusingly the signature of App.map
-- has List, not Html.Html or something
-- App.map TheWordbank (Wordbank.view model.wordbank)


view : Model -> Html Msg
view model =
    let
        wordbank =
            div []
                [ App.map UpdateWordbank (Wordbank.view model.wordbank)
                ]

        progressBar =
            div [ class "progress-bar" ]
                [ App.map UpdateProgressBar (Bar.view model.progressBar) ]

        addInput =
            div [ id "input" ]
                [ input
                    [ placeholder ""
                    , onInput UpdateAddInput
                    , onEnter EnterInput
                    , value model.addInput
                    , id "input-input"
                    , autofocus True
                    ]
                    []
                ]

        enemy =
            div [ id "header" ]
                [ img [ id "enemy", src model.enemyImage ] [] ]

        output =
            div [ id "output-wrapper" ]
                [ div [ id "output" ]
                    [ div [ id "convo" ] (List.map viewRemark model.conversation) ]
                ]
    in
        div [ id "versus-main" ]
            [ enemy
            , progressBar
            , output
            , addInput
            , wordbank
            ]


viewRemark : Remark -> Html.Html Msg
viewRemark remark =
    div [ class "remark" ]
        [ div [ class "insult" ]
            [ text remark.insult ]
        , div [ class "retort" ]
            [ text remark.retort ]
        ]


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


port sendInsult : ( String, Float ) -> Cmd msg


port scrollTop : String -> Cmd msg



-- SUBSCRIPTIONS


port setEnemyImage : (String -> msg) -> Sub msg


port newWordbank : (List String -> msg) -> Sub msg


port suggestions : (List String -> msg) -> Sub msg


port remark : (Remark -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ suggestions Suggest
        , newWordbank NewWordbank
        , remark AddRemark
        , setEnemyImage SetEnemyImage
        , AnimationFrame.times Tick
        ]
