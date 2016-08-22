module Game.View exposing (..)

import Versus.View
import Game.Types exposing (..)
import Menu.View
import Loadout.Loadout as Loadout
import Map.View
import Html exposing (text, div, Html, img, span)
import Html.Attributes exposing (id, class, attribute, src, style)
import Html.App as App


-- VIEW


view : Model -> Html Msg
view model =
    let 
        menu = case model.menuStatus of 
            Hidden ->
                div [id "menu"] []
            _ ->
                div [id "menu"] [App.map UpdateMenu (Menu.View.view model.menu)]


        loadout = case model.loadoutStatus of 
            Hidden ->
                div [id "loadout"] []
            _ ->
                div [id "loadout"] [App.map UpdateLoadout (Loadout.view model.loadout)]


        map = case model.mapStatus of 
            Hidden ->
                div [id "map"] []
            Active ->
                div [id "map"] [App.map UpdateMap (Map.View.view model.map)]
            Inactive ->
                div [id "map"] [App.map UpdateMap (Map.View.viewInactive model.map)]


        versus = case model.versusStatus of
            Hidden ->
                div [id "versus"] []
            _ -> 
                div [id "versus"] [ App.map UpdateVersus (Versus.View.view model.versus) ]

    in
        div [ id "main" ]
            [ map, versus, menu, loadout ]