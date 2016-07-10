port module Encounter exposing (..)

import Versus
import Html.App as App
import Html exposing (div)
import Html.Attributes exposing (id)


main : Program Never
main =
    App.program
        { init = Versus.init [] "" 30
        , update = Versus.update
        , view = view
        , subscriptions = Versus.subscriptions
        }


view : Versus.Model -> Html.Html Versus.Msg
view model =
    div [ id "main" ] [ Versus.view model ]
