port module Main exposing (..)

import Wordbank
import Html exposing (Html, button, div, text, input, Attribute)
import Html.Attributes exposing (value, placeholder, id)
import Html.App as App
import Html.Events exposing (onClick, onInput, keyCode, on)
import Json.Decode as Json


main : Program Never
main =
    App.program
        { init = init [ "Moron", "Gelding" ]
        , update = update
        , view = view
        , subscriptions = subscriptions
        }



-- MODEL


type alias Model =
    { wordbank : Wordbank.Model
    , addInput : String
    , removeInput : String
    , launchInput : String
    , suggestions : Wordbank.Model
    }


init : List String -> ( Model, Cmd Msg )
init words =
    { wordbank = Wordbank.init words
    , addInput = ""
    , removeInput = ""
    , launchInput = ""
    , suggestions = Wordbank.init [ "Go", "Fuck", "Yourself" ]
    }
        ! []



-- UPDATE


type Msg
    = TheWordbank Wordbank.Msg
    | UpdateAddInput String
    | UpdateRemoveInput String
    | Hide String
    | Add String
    | Remove String
    | NoOp
    | LaunchSocket String
    | UpdateLaunchInput String
    | Suggest (List String)
    | Suggestions Wordbank.Msg


update : Msg -> Model -> ( Model, Cmd Msg )
update message model =
    case message of
        TheWordbank msg ->
            { model
                | wordbank = Wordbank.update msg model.wordbank
            }
                ! []

        Suggestions msg ->
            { model
                | suggestions = Wordbank.update msg model.suggestions
            }
                ! []

        UpdateAddInput input ->
            { model | addInput = input } ! []

        UpdateRemoveInput input ->
            { model | removeInput = input } ! []

        UpdateLaunchInput input ->
            { model | launchInput = input } ! []

        NoOp ->
            model ! []

        Hide word ->
            model ! []

        Suggest suggestions ->
            { model | suggestions = Wordbank.init suggestions } ! []

        Add word ->
            { model
                | wordbank = Wordbank.update (Wordbank.Add word) model.wordbank
                , addInput = ""
            }
                ! []

        Remove word ->
            { model
                | wordbank = Wordbank.update (Wordbank.Remove word) model.wordbank
                , removeInput = ""
            }
                ! []

        LaunchSocket word ->
            ( { model | launchInput = "" }, check word )



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
                [ App.map TheWordbank (Wordbank.view model.wordbank)
                ]

        suggestions =
            div []
                [ App.map Suggestions (Wordbank.view model.suggestions)
                ]

        addInput =
            input
                [ placeholder "add"
                , onInput UpdateAddInput
                , onEnter (Add model.addInput)
                , value model.addInput
                ]
                []

        removeInput =
            input
                [ placeholder "remove"
                , onInput UpdateRemoveInput
                , onEnter (Remove model.removeInput)
                , value model.removeInput
                ]
                []

        launchInput =
            input
                [ placeholder "launch"
                , onInput UpdateLaunchInput
                , onEnter (LaunchSocket model.launchInput)
                , value model.launchInput
                ]
                []
    in
        div [ id "main" ]
            [ wordbank
            , addInput
            , removeInput
            , launchInput
            , suggestions
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


port check : String -> Cmd msg



-- SUBSCRIPTIONS


port suggestions : (List String -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    suggestions Suggest
