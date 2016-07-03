port module App exposing (main)

import Html.App as App
import Base exposing (init, update, view, subscriptions)


main : Program Never
main =
    App.program
        { init = init [] "" 30
        , update = update
        , view = view
        , subscriptions = subscriptions
        }
