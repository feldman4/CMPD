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
                    div [ id "encounter" ] [ App.map UpdateEncounter (Versus.view model.encounter) ]

                NoOverlay ->
                    div [ id "empty-overlay" ] [ div [] [] ]

        keyAtt =
            attribute "key" (toString model.key)

        mapImage =
            img [ src model.map.image ] []

        places =
            List.map placeDiv model.map.places
    in
        div [ id "main" ]
            [ div [ class "map", keyAtt ]
                ([ mapImage ] ++ places ++ [ overlay ])
            ]


placeDiv : Place -> Html.Html msg
placeDiv place =
    let
        x =
            .x place |> toPercent

        y =
            .y place |> toPercent

        label =
            ": " ++ (.label place)

        placeStyle =
            style
                [ ( "position", "absolute" )
                , ( "left", x )
                , ( "top", y )
                ]
    in
        div [ placeStyle, class "label" ] [ span [] [ text label ] ]


toPercent : Float -> String
toPercent x =
    (toString (100 * x)) ++ "%"
