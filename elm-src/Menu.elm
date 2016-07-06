module Menu exposing (Model, Tile, Msg(..), init, update, view, subscriptions)

import Html exposing (text, div, Html, span)
import Html.Attributes exposing (id, class, attribute)
import String
import Keyboard
import Char


--import Html.App as App
--main : Program Never
--main =
--    App.program
--        { init = (init tiles "my-menu") ! []
--        , update = (\msg model -> (update msg model) ! [])
--        , view = view
--        , subscriptions = subscriptions
--        }
-- MODEL


type alias Model =
    { tiles : List Tile
    , id : String
    , lastKey : Int
    , active : Bool
    , selected : Bool
    }


type alias Tile =
    { label : String
    , key : Char
    , id : String
    }


init : List Tile -> String -> Model
init tiles id =
    { tiles = tiles
    , id = id
    , lastKey = 0
    , active = True
    , selected = False
    }



-- UPDATE


type Msg
    = KeyPress Int
    | Activate Bool
    | NoOp


update : Msg -> Model -> ( Model, Maybe Char )
update msg model =
    case msg of
        KeyPress key ->
            if model.active then
                if key == model.lastKey then
                    ( model, Just (Char.fromCode model.lastKey) )
                else
                    ( { model | lastKey = key }, Nothing )
            else
                ( model, Nothing )

        Activate bool ->
            ( { model | active = bool }, Nothing )

        NoOp ->
            ( model, Nothing )



-- VIEW


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


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Keyboard.presses KeyPress ]
