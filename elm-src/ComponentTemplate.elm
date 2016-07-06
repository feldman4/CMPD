module ComponentTemplate exposing (Model, Msg(..), init, update, view)

import Html exposing (text, div)
import Html.Attributes exposing (id, class)
import Html.Events exposing (onClick, onInput, keyCode, on)
import Html.App as App


--main : Program Never
--main =
--    App.program
--        { init = init [] "" 30
--        , update = update
--        , view = view
--        , subscriptions = subscriptions
--        }
-- MODEL


type alias Model =
    { field : String
    }


init : String -> Model
init initialField =
    { field = initialField
    }



-- UPDATE


type Msg
    = Response String
    | NoOp


update : Msg -> Model -> Model
update msg model =
    case msg of
        Response newField ->
            { model
                | field = newField
            }

        NoOp ->
            model



-- VIEW


view : Model -> Html Msg
view model =
    div [ id "field", class "field" ] [ text model.field ]
