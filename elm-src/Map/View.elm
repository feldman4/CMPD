module Map.View exposing (..)

import Map.Types exposing (..)
import Menu.View
import Html exposing (text, div, Html, img, span)
import Html.Attributes exposing (id, class, attribute, src, style)
import Html.App as App
import String
import Markdown


-- VIEW


view : Model -> Html Msg
view model =
    let
        overlay =
            div [ id "empty-overlay" ]
                [ App.map UpdateMenu (Menu.View.viewMap model.menu) ]
    in
        div [ class "map" ] [ img [ src model.map.image ] [], overlay ]


viewInactive : Model -> Html Msg
viewInactive model =
    div [ class "map" ] [ img [ src model.map.image ] [] ]


viewGutter : Model -> Html Msg
viewGutter model =
    let
        lastKey =
            String.fromChar model.menu.lastKey

        gutterText =
            List.filter (\p -> p.key == lastKey) model.map.places
                |> List.map .preview
                |> List.head
                |> (Maybe.withDefault model.map.intro)
    in
        Markdown.toHtml [] gutterText
