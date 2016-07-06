module View exposing (..)

import Versus
import Model exposing (..)
import Menu
import Html exposing (text, div, Html, img)
import Html.Attributes exposing (id, class, attribute, src)
import Html.App as App


-- VIEW


view : Model -> Html Msg
view model =
    let
        overlay =
            case model.overlay of
                MenuOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateMenu (Menu.view model.menu) ]

                LoadoutOverlay ->
                    div [ id "overlay" ]
                        [ App.map UpdateLoadout (Menu.view model.loadout) ]

                EncounterOverlay ->
                    div [ id "encounter" ] [ App.map UpdateEncounter (Versus.view model.encounter) ]

                NoOverlay ->
                    div [ id "empty-overlay" ] [ div [] [] ]

        keyAtt =
            attribute "key" (toString model.key)
    in
        div [ class "map", id model.image, keyAtt ]
            ([ img [ src model.image ] []
             , overlay
             ]
            )
