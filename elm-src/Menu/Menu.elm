module Menu.Menu exposing (init, update, subscriptions)

import Menu.Types exposing (..)
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


init : List Tile -> String -> Model
init tiles id =
    { tiles = tiles
    , lastKey = ' '
    , id = id
    }



-- UPDATE


update : Msg -> Model -> ( Model, Maybe Char )
update msg model =
    case msg of
        KeyPress key ->
            let
                code =
                    Char.fromCode key
            in
                if code == model.lastKey then
                    ( model, Just model.lastKey )
                else
                    ( { model | lastKey = code }, Nothing )

        NoOp ->
            ( model, Nothing )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Keyboard.presses KeyPress ]
