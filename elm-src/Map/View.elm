module Map.View exposing (..)

import Versus
import Map.Types exposing (..)
import Menu.View
import Loadout.Loadout as Loadout
import Html exposing (text, div, Html, img, span)
import Html.Attributes exposing (id, class, attribute, src, style)
import Html.App as App


-- VIEW


view : Model -> Html Msg
view model =
    let
        overlay =
            case model.overlay of
                MenuOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateMenu (Menu.View.view model.menu) ]

                WeaponsOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateWeapons (Menu.View.view model.weapons) ]

                LoadoutOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateLoadout (Loadout.view model.loadout) ]

                EncounterOverlay char ->
                    div [ id "encounter" ]
                        [ App.map UpdateEncounter (Versus.view model.encounter) ]

                NoOverlay ->
                    div [ id "empty-overlay" ]
                        [ App.map UpdateMapMenu (Menu.View.viewMap model.mapMenu) ]

        keyAtt =
            attribute "key" (toString model.key)

        mapDiv =
            if False then
                div [ class "map", keyAtt ]
                    [ img [ src model.map.image ] [ overlay ] ]
            else
                div [ class "map", keyAtt ]
                    ([ img [ src model.map.image ] [], overlay ])
    in
        div [ id "main" ]
            [ mapDiv ]
