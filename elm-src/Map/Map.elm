port module Map.Map exposing (..)

import Map.View exposing (view)
import Map.Types exposing (..)
import Menu.Types exposing (Tile)
import Menu.Menu as Menu
import Html.App as App
import String
import List


main : Program Never
main =
    App.program
        { init = init testMap ! []
        , update = programUpdate
        , view = view
        , subscriptions = subscriptions
        }


programUpdate : Msg -> Model -> ( Model, Cmd Msg )
programUpdate msg model =
    let
        ( newModel, newMsg, selection ) =
            update msg model
    in
        ( newModel, newMsg )


init : Map -> Model
init map =
    let
        tiles =
            List.map placeToTile map.places

        model =
            { map = map
            , menu = Menu.init tiles "map-menu"
            }
    in
        model


testMap : Map
testMap =
    { image = "static/images/islands.png"
    , name = "test"
    , places = testPlaces
    , intro = "a test map"
    }


placeToTile : Place -> Tile
placeToTile place =
    { x = place.x
    , y = place.y
    , label = place.label
    , key = stringToChar place.key
    }


stringToChar : String -> Char
stringToChar input =
    case String.uncons input of
        Just ( c, s ) ->
            c

        Nothing ->
            ' '


testPlaces : List Place
testPlaces =
    [ { label = "your", key = "y", x = 0, y = 0, preview = "one" }
    , { label = "mums", key = "m", x = 0.5, y = 0, preview = "two" }
    , { label = "house", key = "h", x = 0, y = 0.5, preview = "three" }
    ]



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg, Maybe String )
update msg model =
    case msg of
        UpdateMenu msg ->
            let
                ( newMenu, selection ) =
                    Menu.update msg model.menu

                newModel =
                    { model | menu = newMenu }
            in
                case selection of
                    Nothing ->
                        ( newModel, Cmd.none, Nothing )

                    Just char ->
                        let
                            label =
                                List.filter (\tile -> tile.key == char) model.menu.tiles
                                    |> List.map .label
                                    |> List.head
                        in
                            ( newModel, Cmd.none, label )



--OUTGOING
-- INCOMING


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        ]
