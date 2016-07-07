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
    , id = id
    , lastKey = 0
    , active = True
    , selected = False
    }



-- UPDATE


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


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Keyboard.presses KeyPress ]
