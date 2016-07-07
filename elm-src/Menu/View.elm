module Menu.View exposing (view)

import Menu.Types exposing (..)
import Html exposing (text, div, Html, span)
import Html.Attributes exposing (id, class, attribute)
import String
import Char


view : Model -> Html Msg
view model =
    let
        lastKeyAtt =
            attribute "lastKey" (toString model.lastKey)

        flagAtt =
            attribute "selected" (toString model.selected)
    in
        div [ id model.id, class "menu", lastKeyAtt, flagAtt ]
            (List.map (\t -> viewTile t (Char.toCode t.key == model.lastKey))
                model.tiles
            )


viewTile : Tile -> Bool -> Html Msg
viewTile tile selected =
    let
        tag =
            if selected then
                " selected"
            else
                ""
    in
        div [ id tile.id, class ("tile " ++ tile.label ++ tag) ]
            [ div [ class "tile-key" ] [ span [] [ text (String.fromChar tile.key) ] ]
            , div [ class "tile-label" ] [ span [] [ text tile.label ] ]
            ]
