module Wordbank exposing (Model, Msg(..), init, update, view)

import Html exposing (..)
import Html.Attributes exposing (..)
import List


-- MODEL


type alias Model =
    { words : List ( String, Bool )
    , maxToDisplay : Int
    }


init : List String -> Int -> Model
init words maxToDisplay =
    { words = List.map (\x -> ( x, True )) words
    , maxToDisplay = maxToDisplay
    }



-- UPDATE


type Msg
    = Hide String
    | Show String
    | Toggle String
    | HideAll
    | ShowAll
    | Add String
    | Remove String
    | ShowWords (List String)


type ChangeIt
    = On
    | Off
    | Flip


update : Msg -> Model -> Model
update msg model =
    case msg of
        Hide word ->
            { model
                | words = toggleWord Off word model.words
            }

        Show word ->
            { model
                | words = toggleWord On word model.words
            }

        Toggle word ->
            { model
                | words = toggleWord Flip word model.words
            }

        HideAll ->
            { model | words = toggleWords Off model.words }

        ShowAll ->
            { model | words = toggleWords On model.words }

        Add word ->
            { model
                | words = model.words ++ [ ( word, True ) ]
            }

        Remove word ->
            { model
                | words = List.filter (\( w, b ) -> w /= word) model.words
            }

        ShowWords wordsToShow ->
            { model
                | words =
                    let
                        ( show, dontShow ) =
                            List.partition (\w -> List.member w wordsToShow) (List.map fst model.words)

                        sortedShow =
                            List.filter (\w -> List.member w show) wordsToShow

                        allWords =
                            (List.map (\w -> ( w, True )) sortedShow)
                                ++ (List.map (\w -> ( w, False )) dontShow)
                    in
                        allWords
                    --let
                    --    hidden =
                    --        (toggleWords Off model.words)
                    --in
                    --    List.foldl (\w words -> toggleWord On w words) hidden wordsToShow
            }


toggleWords : ChangeIt -> List ( String, Bool ) -> List ( String, Bool )
toggleWords state words =
    List.map
        (\( w, b ) ->
            case state of
                On ->
                    ( w, True )

                Off ->
                    ( w, False )

                Flip ->
                    ( w, not b )
        )
        words


toggleWord : ChangeIt -> String -> List ( String, Bool ) -> List ( String, Bool )
toggleWord state word words =
    List.map
        (\( w, b ) ->
            if w == word then
                case state of
                    On ->
                        ( w, True )

                    Off ->
                        ( w, False )

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
            div [ id "wordbank" ]
                (List.take model.maxToDisplay
                    (List.filterMap viewWord model.words)
                )
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
