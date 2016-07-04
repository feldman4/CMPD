port module Base exposing (..)

import Wordbank
import Html exposing (Html, button, div, text, img, input, Attribute)
import Html.Attributes exposing (value, placeholder, id, src, class, autofocus)
import Html.App as App
import Html.Events exposing (onClick, onInput, keyCode, on)
import Json.Decode as Json


main : Program Never
main =
    App.program
        { init = init [] "" 30
        , update = update
        , view = view
        , subscriptions = subscriptions
        }



-- MODEL


type alias Model =
    { wordbank : Wordbank.Model
    , addInput : String
    , enemyImage : String
    , maxToDisplay : Int
    , conversation : List Remark
    }


type alias Remark =
    { insult : String
    , retort : String
    }


init : List String -> String -> Int -> ( Model, Cmd Msg )
init words enemyImage maxToDisplay =
    let
        model =
            { wordbank = Wordbank.init [] 0
            , enemyImage = enemyImage
            , maxToDisplay = maxToDisplay
            , addInput = ""
            , conversation = []
            }
    in
        update (NewWordbank words) model



-- UPDATE


type Msg
    = NoOp
    | NewWordbank (List String)
    | UpdateWordbank Wordbank.Msg
    | UpdateAddInput String
    | AskSuggestions String
    | Suggest (List String)
    | EnterInput
    | AddRemark Remark
    | SetEnemyImage String


update : Msg -> Model -> ( Model, Cmd Msg )
update message model =
    case message of
        NoOp ->
            model ! []

        NewWordbank words ->
            { model | wordbank = Wordbank.init words model.maxToDisplay } ! []

        UpdateWordbank msg ->
            { model
                | wordbank = Wordbank.update msg model.wordbank
            }
                ! []

        UpdateAddInput input ->
            update (AskSuggestions input) { model | addInput = input }

        AskSuggestions word ->
            ( model, check ( word, List.map fst model.wordbank.words ) )

        Suggest suggestions ->
            { model
                | wordbank =
                    Wordbank.update (Wordbank.ShowWords suggestions)
                        model.wordbank
            }
                ! []

        EnterInput ->
            let
                maybe =
                    List.head
                        (List.map fst
                            (List.filter (\( w, b ) -> b) model.wordbank.words)
                        )
            in
                case maybe of
                    Just word ->
                        ( { model | addInput = "" }, send word )

                    Nothing ->
                        model ! []

        AddRemark remark ->
            ( { model | conversation = model.conversation ++ [ remark ] }
            , scrollTop "#output"
            )

        SetEnemyImage src ->
            { model | enemyImage = src } ! []


showWordbankWord : String -> Wordbank.Model -> Wordbank.Model
showWordbankWord word model =
    Wordbank.update (Wordbank.Show word) model



-- VIEW
-- the following tags the Html Msg bag coming out of model.wordbank with
-- the new type TheWordbank so it can be matched and processed by
-- this model's update function. confusingly the signature of App.map
-- has List, not Html.Html or something
-- App.map TheWordbank (Wordbank.view model.wordbank)


view : Model -> Html Msg
view model =
    let
        wordbank =
            div []
                [ App.map UpdateWordbank (Wordbank.view model.wordbank)
                ]

        addInput =
            div [ id "input" ]
                [ input
                    [ placeholder ""
                    , onInput UpdateAddInput
                    , onEnter EnterInput
                    , value model.addInput
                    , id "input-input"
                    , autofocus True
                    ]
                    []
                ]

        enemy =
            div [ id "header" ]
                [ img [ id "enemy", src model.enemyImage ] [] ]

        output =
            div [ id "output" ]
                [ div [ id "convo" ] (List.map viewRemark model.conversation) ]
    in
        div [ id "main" ]
            [ enemy
            , output
            , addInput
            , wordbank
            ]


viewRemark : Remark -> Html.Html Msg
viewRemark remark =
    div [ class "remark" ]
        [ div [ class "insult" ]
            [ text remark.insult ]
        , div [ class "retort" ]
            [ text remark.retort ]
        ]


onEnter : Msg -> Attribute Msg
onEnter msg =
    let
        tagger code =
            if code == 13 then
                msg
            else
                NoOp
    in
        on "keydown" (Json.map tagger keyCode)



-- OUTGOING


port check : ( String, List String ) -> Cmd msg


port send : String -> Cmd msg


port scrollTop : String -> Cmd msg



-- SUBSCRIPTIONS


port newWordbank : (List String -> msg) -> Sub msg


port suggestions : (List String -> msg) -> Sub msg


port remark : (Remark -> msg) -> Sub msg


port setEnemyImage : (String -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ suggestions Suggest
        , newWordbank NewWordbank
        , remark AddRemark
        , setEnemyImage SetEnemyImage
        ]
