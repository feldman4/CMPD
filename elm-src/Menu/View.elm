module Menu.View exposing (view, viewMap)

import Menu.Types exposing (..)
import Html exposing (text, div, Html, span, img)
import Html.Attributes exposing (id, class, attribute, style, src)
import String
import Char


view : Model -> Html Msg
view model =
    let
        lastKeyAtt =
            attribute "lastKey" (toString model.lastKey)

        getTileContents =
            (\t -> viewTile t (Char.toCode t.key == model.lastKey))
    in
        div [ id model.id, class "menu", lastKeyAtt ]
            (List.map getTileContents model.tiles)



-- map-style view on menu, determine selected by comparing Model.lastKey to
-- first Char in place.label


viewMap : Model -> Html Msg
viewMap model =
    let
        lastKeyAtt =
            attribute "lastKey" (toString model.lastKey)

        getTileContents =
            (\t -> viewTileXY t (Char.toCode t.key == model.lastKey))
    in
        div [ id model.id, class "map-menu", lastKeyAtt ]
            (List.map getTileContents model.tiles)
        
        


-- helper functions


viewTile : Tile -> Bool -> Html Msg
viewTile tile selected =
    let
        tag =
            if selected then
                " selected"
            else
                ""
    in
        div [ class ("tile " ++ tile.label ++ tag) ]
            [ div [ class "tile-key" ] [ span [] [ text (String.fromChar tile.key) ] ]
            , div [ class "tile-label" ] [ span [] [ text tile.label ] ]
            ]


viewTileXY : Tile -> Bool -> Html.Html msg
viewTileXY tile selected =
    let
        tag =
            if selected then
                " selected"
            else
                ""

        placeStyle =
            style
                [ ( "position", "absolute" )
                , ( "left", tile.x |> toPercent )
                , ( "top", tile.y |> toPercent )
                ]
    in
        div [ class ("tile " ++ tile.label ++ tag), placeStyle ]
            [ div [ class "tile-key" ] [ span [] [ text (String.fromChar tile.key) ] ]
            , div [ class "tile-label" ] [ span [] [ text tile.label ] ]
            ]


toPercent : Float -> String
toPercent x =
    (toString (100 * x)) ++ "%"
