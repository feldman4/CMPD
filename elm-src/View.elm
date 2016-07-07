module View exposing (..)

import Versus
import Model exposing (..)
import Menu.Menu as Menu
import Menu.Types
import Menu.View
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

                LoadoutOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateLoadout (Menu.View.view model.loadout) ]

                EncounterOverlay ->
                    div [ id "encounter" ]
                        [ App.map UpdateEncounter (Versus.view model.encounter) ]

                NoOverlay ->
                    div [ id "empty-overlay" ]
                        [ App.map UpdateMapMenu (Menu.View.viewMap model.mapMenu) ]

        keyAtt =
            attribute "key" (toString model.key)

        mapImage =
            img [ src model.map.image ] []
    in
        div [ id "main" ]
            [ div [ class "map", keyAtt ]
                ([ mapImage, overlay ])
            ]
