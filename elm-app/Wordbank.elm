module Wordbank exposing (Model, Msg(..), init, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput, keyCode, on)
import List
import Html.App as App


{--
main =
    App.beginnerProgram
        { model = init [ "Hello", "Fuck You" ]
        , update = update
        , view = view
        }
--}
-- MODEL


type alias Model =
    { words : List ( String, Bool )
    }


init : List String -> Model
init words =
    { words = List.map (\x -> ( x, True )) words
    }



-- UPDATE


type Msg
    = Hide String
    | Show String
    | Toggle String
    | ShowAll
    | HideAll
    | Add String
    | Remove String


type ChangeIt
    = On
    | Off
    | Flip


update : Msg -> Model -> Model
update msg model =
    case msg of
        Hide word ->
            { model
                | words = toggleWord On word model.words
            }

        Show word ->
            { model
                | words = toggleWord Off word model.words
            }

        Toggle word ->
            { model
                | words = toggleWord Flip word model.words
            }

        ShowAll ->
            { model | words = List.map (\( x, _ ) -> ( x, True )) model.words }

        HideAll ->
            { model | words = List.map (\( x, _ ) -> ( x, False )) model.words }

        Add word ->
            { model
                | words = model.words ++ [ ( word, True ) ]
            }

        Remove word ->
            { model
                | words = List.filter (\( w, b ) -> w /= word) model.words
            }


toggleWord : ChangeIt -> String -> List ( String, Bool ) -> List ( String, Bool )
toggleWord state word words =
    List.map
        (\( w, b ) ->
            if w == word then
                case state of
                    On ->
                        ( w, False )

                    Off ->
                        ( w, True )

                    Flip ->
                        ( w, not b )
            else
                ( w, b )
        )
        words



-- VIEW


view : Model -> Html Msg
view model =
    let
        wordbank =
            div [ id "wordbank" ] (List.filterMap viewWord model.words)
    in
        wordbank


viewWord : ( String, Bool ) -> Maybe (Html.Html msg)
viewWord ( word, show ) =
    case show of
        True ->
            Just (div [ class "word" ] [ text word ])

        False ->
            Nothing


countStyle : Attribute msg
countStyle =
    style
        [ ( "font-size", "20px" )
        , ( "font-family", "monospace" )
        , ( "display", "inline-block" )
        , ( "width", "50px" )
        , ( "text-align", "center" )
        ]
