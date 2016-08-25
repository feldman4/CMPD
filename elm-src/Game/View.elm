module Game.View exposing (..)

import Versus.View
import Game.Types exposing (..)
import Menu.View
import Loadout.Loadout as Loadout
import Message.Message as Message
import Map.View
import Html exposing (text, div, Html, img, span)
import Html.Attributes exposing (id, class, attribute, src, style)
import Html.App as App


-- VIEW


view : Model -> Html Msg
view model =
    let
        message = 
            case model.messageStatus of
                Active ->
                    div [ id "message" ] [App.map UpdateMessage (Message.view model.message)]
                _ -> 
                    div [ id "message" ] []

        options =
            case model.menuStatus of
                Hidden ->
                    div [] []

                _ ->
                    App.map UpdateMenu (Menu.View.view model.menu)

        loadout =
            case model.loadoutStatus of
                Hidden ->
                    div [] []

                _ ->
                    div [ id "loadout" ] [ App.map UpdateLoadout (Loadout.view model.loadout) ]

        menu =
                if model.menuStatus == Hidden
                && model.loadoutStatus == Hidden then
                    div [] []
                else
                   div [ id "menu" ] [ options, loadout ]

        map =
            case model.mapStatus of
                Hidden ->
                    div [ class "map" ] []

                Active ->
                    App.map UpdateMap (Map.View.view model.map)

                Inactive ->
                    App.map UpdateMap (Map.View.viewInactive model.map)

        versus =
            case model.versusStatus of
                Hidden ->
                    div [ id "versus" ] []

                _ ->
                    App.map UpdateVersus (Versus.View.view model.versus)

        gutter =
            case model.mapStatus of
                Hidden ->
                    div [ id "gutter" ] []

                Active ->
                    div [ id "gutter"] [App.map UpdateMap (Map.View.viewGutter model.map)]

                Inactive ->
                    div [ id "gutter" ] []
    in
        div [ id "main" ]
            [ map, versus, message, menu, gutter ]
