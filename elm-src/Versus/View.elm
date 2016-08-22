module Versus.View exposing (..)

import Bar
import Wordbank exposing (Word)
import Versus.Types exposing (..)
import Html exposing (Html, button, div, text, img, input, Attribute)
import Html.Attributes exposing (value, placeholder, id, src, class, autofocus, itemprop)
import Html.App as App
import Html.Events exposing (onClick, onInput, keyCode, on)
import Json.Decode as Json


-- VIEW
-- the following tags the Html Msg bag coming out of model.wordbank with
-- the new type TheWordbank so it can be matched and processed by
-- this model's update function. confusingly the signature of App.map
-- has List, not Html.Html or something
-- App.map TheWordbank (Wordbank.view model.wordbank)


viewSimple : Model -> Html Msg
viewSimple model =
    let
        wordbank =
            App.map UpdateWordbank (Wordbank.view model.wordbank)

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
                [ img [ id "enemy", src model.enemy.image ] [] ]

        output =
            div [ id "output" ]
                [ div [ id "convo" ] (List.map viewRemark (List.reverse model.conversation))
                , div [ id "shield" ] []
                ]
    in
        div [ id "versus-main" ]
            [ enemy
            , progressBar
            , output
            , addInput
            , wordbank
            ]

viewMain : Model -> Html Msg
viewMain model = 
    let
        versus = 
            view model
    in
        div [id "main"] [versus]


view : Model -> Html Msg
view model =
    let
        wordbank =
            App.map UpdateWordbank (Wordbank.view model.wordbank)

        statusPlayer =
            div [ class "status" ]
                [ div [ class "name" ] [ text "player" ]
                , div [ class "progress-bar" ]
                    [ App.map UpdateProgressBar (Bar.view model.progressBar) ]
                , div [ class "arrow" ] []
                ]

        statusEnemy =
            div [ class "status" ]
                [ div [ class "name" ] [ text model.enemy.name ]
                , div [ class "progress-bar" ]
                    [ App.map UpdateProgressBar (Bar.view model.progressBar) ]
                , div [ class "arrow" ] []
                ]

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
            img [ src model.enemy.image ] []

        player =
            img [ src model.player.image ] []

        output =
            div [ id "output" ]
                [ div [ id "convo" ] (List.map viewRemarkScore (List.reverse model.conversation))
                , div [ id "shield" ] []
                ]
    in
        div [ id "versus-main" ]
            [ div [ id "top-half" ]
                [ div [ class "enemy" ] [ statusEnemy, enemy ]
                , div [ class "player" ] [ player, statusPlayer ]
                ]
            , div [ id "bottom-half" ]
                [ div [ id "bottom-left" ]
                    [ addInput
                    , wordbank
                    ]
                , div [ id "bottom-right" ]
                    [ output ]
                ]
            ]


viewRemarkScore : Remark -> Html.Html Msg
viewRemarkScore remark =
    div [ class "remark" ]
        [ div [ class "insult" ]
            [ div [ class "insult-phrase" ] [ text remark.insult ]
            , div [ class "insult-score" ] [ text <| toString remark.score ]
            ]
        , div [ class "retort" ]
            [ div [ class "retort-score" ] [ text <| toString remark.score ]
            , div [ class "retort-phrase" ] [ text remark.retort ]
            ]
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
