port module Loadout.Loadout
    exposing
        ( Model
        , Msg(..)
        , init
        , initFromLongform
        , update
        , view
        , subscriptions
        )

import Wordbank exposing (Word)
import Html exposing (text, div, span)
import Html.Attributes exposing (id, class)
import Html.App as App
import Keyboard
import List
import List.Extra


main : Program Never
main =
    App.program
        { init = init [] dummyWords dummyCapacity ! []
        , update = update
        , view = view
        , subscriptions = subscriptions
        }


dummyWords : List Word
dummyWords =
    let
        makeWord word pos =
            { word = word, partOfSpeech = pos, tag = "" }

        words =
            [ ( "Chunky", "Adjective" )
            , ( "Unregenerate", "Adjective" )
            , ( "Ridiculous", "Adjective" )
            , ( "Horse Thief", "Noun" )
            , ( "Coward", "Noun" )
            , ( "Johnny-Come-Lately", "Noun" )
            , ( "Buffoon", "Noun" )
            , ( "French", "Adjective" )
            ]
    in
        List.map (\( w, p ) -> makeWord w p) words


dummyCapacity : List ( String, Int )
dummyCapacity =
    [ ( "Adjective", 3 ), ( "Noun", 3 ) ]



--MODEL


init : List Word -> List Word -> List ( String, Int ) -> Model
init loaded unloaded capacity =
    { loaded = sortWords loaded
    , unloaded = sortWords unloaded
    , selected = Maybe.withDefault nullWord (List.head (loaded ++ unloaded))
    , total = List.length (loaded ++ unloaded)
    , partsOfSpeech = List.Extra.unique (List.map (\w -> w.partOfSpeech) (loaded ++ unloaded))
    , capacity = capacity
    , key = 0
    }


initFromLongform : List ( String, String, Bool ) -> Model
initFromLongform words =
    let
        convert predicate words =
            words
                |> List.sortBy (\( pos, word, load ) -> ( pos, word ))
                |> List.filter predicate
                |> List.map (\( pos, word, load ) -> { word = word, partOfSpeech = pos, tag = "wordTag" })

        loaded =
            convert (\( pos, word, load ) -> load) words

        unloaded =
            convert (\( pos, word, load ) -> not load) words

        partsOfSpeech =
            words
                |> List.map (\( pos, word, load ) -> pos)
                |> List.Extra.unique

        selected =
            words
                |> convert (\( pos, word, load ) -> True)
                |> List.head
                |> Maybe.withDefault nullWord
    in
        { loaded = loaded
        , unloaded = unloaded
        , selected = selected
        , total = List.length words
        , partsOfSpeech = partsOfSpeech
        , key = 0
        , capacity = []
        }


sortWords : List Word -> List Word
sortWords words =
    List.sortBy (\w -> w.word) words


sortWordsTuple : List ( Word, a ) -> List ( Word, a )
sortWordsTuple words =
    words
        |> List.indexedMap (\i ( w, a ) -> ( w.word, i ))
        |> List.sort
        |> List.map (\( w, i ) -> List.Extra.getAt i words)
        |> List.filterMap identity


nullWord : Word
nullWord =
    { word = "null", partOfSpeech = "Noun", tag = "nullWordTag" }


type alias Model =
    { loaded : List Word
    , unloaded : List Word
    , selected : Word
    , total : Int
    , partsOfSpeech : List String
    , key : Int
    , capacity : List ( String, Int )
    }


type Msg
    = Select
    | KeyPress Int



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        KeyPress key ->
            let
                thisPos =
                    model.selected.partOfSpeech

                posWords pos =
                    (model.loaded ++ model.unloaded)
                        |> List.filter (\w -> w.partOfSpeech == pos)
                        |> sortWords

                ( up, down ) =
                    getBeforeAfter (\w -> w /= model.selected) (posWords thisPos) model.selected

                ( before, after ) =
                    getBeforeAfter (\pos -> pos /= thisPos) model.partsOfSpeech thisPos

                getWord pos =
                    case List.head (posWords pos) of
                        Just word ->
                            word

                        Nothing ->
                            model.selected

                left =
                    getWord before

                right =
                    getWord after
            in
                if key == keycode.up then
                    { model | selected = up } ! []
                else if key == keycode.down then
                    { model | selected = down } ! []
                else if key == keycode.left then
                    { model | selected = left } ! []
                else if key == keycode.right then
                    { model | selected = right } ! []
                else if key == 115 then
                    update Select model
                else
                    { model | key = key } ! []

        Select ->
            let
                thisPos =
                    model.selected.partOfSpeech

                capacity =
                    getPosCapacity model thisPos

                used =
                    model.loaded
                        |> List.filter (\w -> w.partOfSpeech == thisPos)
                        |> List.length

                ( newLoaded, newUnloaded ) =
                    if List.member model.selected model.loaded then
                        ( List.Extra.remove model.selected model.loaded
                        , sortWords (model.unloaded ++ [ model.selected ])
                        )
                    else
                        ( sortWords (model.loaded ++ [ model.selected ])
                        , List.Extra.remove model.selected model.unloaded
                        )
            in
                if
                    (List.member model.selected model.unloaded)
                        && used
                        == capacity
                then
                    model ! []
                else
                    { model | loaded = newLoaded, unloaded = newUnloaded } ! []


getPosCapacity : Model -> String -> Int
getPosCapacity model thisPos =
    model.capacity
        |> List.filter (\( pos, c ) -> pos == thisPos)
        |> List.head
        |> Maybe.withDefault ( "null", 100 )
        |> snd


getBeforeAfter : (a -> Bool) -> List a -> a -> ( a, a )
getBeforeAfter predicate list backup =
    let
        ( x, y ) =
            List.Extra.span predicate list

        before =
            case List.Extra.last (y ++ x) of
                Just a ->
                    a

                Nothing ->
                    backup

        after =
            case List.tail (y ++ x ++ y) `Maybe.andThen` List.head of
                Just a ->
                    a

                Nothing ->
                    backup
    in
        ( before, after )


port scrollTop : String -> Cmd msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [ Keyboard.presses KeyPress ]


keycode :
    { escape : Int
    , shift : Int
    , space : Int
    , enter : Int
    , left : Int
    , up : Int
    , right : Int
    , down : Int
    }
keycode =
    { enter = 13
    , shift = 16
    , space = 32
    , escape = 27
    , left = 106
    , up = 105
    , right = 108
    , down = 107
    }



-- VIEW


view : Model -> Html.Html Msg
view model =
    let
        divPOS =
            List.map (\p -> viewPOS p model) model.partsOfSpeech
    in
        div [ id "loadout" ] divPOS


viewPOS : String -> Model -> Html.Html Msg
viewPOS pos model =
    let
        selected =
            model.selected

        loaded =
            List.map (\w -> ( w, True )) model.loaded

        unloaded =
            List.map (\w -> ( w, False )) model.unloaded

        words =
            loaded ++ unloaded

        wordsWithPOS =
            words
                |> List.filter (\( w, b ) -> w.partOfSpeech == pos)
                |> sortWordsTuple

        wordsDiv =
            div [ class "words" ]
                ((List.map (\( word, load ) -> viewWord word load (word == selected))
                    wordsWithPOS
                 )
                    ++ [ div [ class "scroll-dummy" ] [] ]
                )

        capacity =
            getPosCapacity model pos

        used =
            model.loaded
                |> List.filter (\w -> w.partOfSpeech == pos)
                |> List.length

        capacityDiv =
            div [ class "capacity" ]
                ((List.repeat used (div [ class "led used" ] []))
                    ++ (List.repeat (capacity - used) (div [ class "led unused" ] []))
                )

        headingDiv =
            div [ class "heading" ] [ (span [] [ text pos ]), capacityDiv ]

        posIndex =
            case (List.Extra.elemIndex pos model.partsOfSpeech) of
                Just i ->
                    i + 1 |> toString

                Nothing ->
                    "0"
    in
        div [ class ("pane " ++ pos ++ " pos-" ++ posIndex) ]
            [ headingDiv, wordsDiv ]


viewWord : Word -> Bool -> Bool -> Html.Html Msg
viewWord word load select =
    let
        tagLoad =
            if load then
                " loaded"
            else
                " unloaded"

        tagSelect =
            if select then
                " selected"
            else
                ""
    in
        div [ class ("word " ++ word.partOfSpeech ++ tagLoad ++ tagSelect) ]
            [ span [] [ text word.word ] ]
