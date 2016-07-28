module Wordbank exposing (Model, Msg(..), init, update, view, Word)

import Html exposing (..)
import Html.Attributes exposing (..)
import List
import String


-- MODEL


type alias Model =
    { words : List ( Word, Bool )
    , maxToDisplay : Int
    }


init : List Word -> Int -> Model
init words maxToDisplay =
    { words = List.map (\x -> ( x, True )) words
    , maxToDisplay = maxToDisplay
    }


type alias Word = 
    { word : String,
      partOfSpeech: String,
      tag: String
  }

-- UPDATE


type Msg
    = Hide Word
    | Show Word
    | Toggle Word
    | HideAll
    | ShowAll
    | Add Word
    | Remove Word
    | ShowWords (List Word)


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


toggleWords : ChangeIt -> List ( Word, Bool ) -> List ( Word, Bool )
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


toggleWord : ChangeIt -> Word -> List ( Word, Bool ) -> List ( Word, Bool )
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


viewWord : ( Word, Bool ) -> Maybe (Html.Html msg)
viewWord ( word, show ) =
    let
        wordClass = String.join " " ["word", word.partOfSpeech, word.tag]
    in
        case show of
            True ->
                Just (div [ class wordClass ] [ text word.word ])

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
