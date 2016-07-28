port module Versus exposing (..)

import Bar
import Wordbank exposing (Word)
import Html exposing (Html, button, div, text, img, input, Attribute)
import Html.Attributes exposing (value, placeholder, id, src, class, autofocus, itemprop)
import Html.App as App
import Html.Events exposing (onClick, onInput, keyCode, on)
import Json.Decode as Json
import Time
import AnimationFrame


main : Program Never
main =
    let
        words =
            []

        enemyImage =
            ""

        maxToDisplay =
            30
    in
        App.program
            { init = init words enemyImage maxToDisplay
            , update = update
            , view = view
            , subscriptions = subscriptions
            }



-- MODEL


type alias Model =
    { wordbank : Wordbank.Model
    , progressBar : Bar.Model
    , addInput : String
    , enemyImage : String
    , maxToDisplay : Int
    , conversation : List Remark
    , clock : Time.Time
    , firstTick : Bool
    , overload : Float
    , drainRate : Float -- 0.02 works
    }


init : List Word -> String -> Int -> ( Model, Cmd Msg )
init words enemyImage maxToDisplay =
    let
        model =
            { wordbank = Wordbank.init [] 0
            , progressBar = Bar.init 0.5 True
            , enemyImage = enemyImage
            , maxToDisplay = maxToDisplay
            , addInput = ""
            , conversation = []
            , clock = 0
            , firstTick = True
            , overload = 0.833
            , drainRate = 0
            }
    in
        update (NewWordbank words) model


type alias Remark =
    { insult : String
    , retort : String
    , score : Float
    }


inputID : String
inputID =
    "#input-input"



-- UPDATE


type Msg
    = NoOp
    | NewWordbank (List Word)
    | UpdateWordbank Wordbank.Msg
    | UpdateAddInput String
    | AskSuggestions String
    | Suggest (List String)
    | EnterInput
    | AddRemark Remark
    | SetEnemyImage String
    | UpdateProgressBar Bar.Msg
    | Tick Time.Time


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

        UpdateProgressBar msg ->
            { model
                | progressBar = Bar.update msg model.progressBar
            }
                ! []

        UpdateAddInput input ->
            update (AskSuggestions input) { model | addInput = input }

        AskSuggestions word ->
            ( model, askFuse ( word, List.map (\(w, visible) -> w.word) model.wordbank.words ) )

        Suggest suggestions ->
            let 
                wordbankWords = model.wordbank.words

                suggestionWords = List.filter (\(w, visible) -> List.member w.word suggestions) wordbankWords 
                        |> List.map (\(w, visible) -> w)
            in
            { model
                | wordbank =
                    Wordbank.update (Wordbank.ShowWords suggestionWords)
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
                        ( { model | addInput = "" }, sendInsult ( word, model.progressBar.value ) )

                    Nothing ->
                        model ! []

        AddRemark remark ->
            let
                progress =
                    max (min (model.progressBar.value + remark.score) 1) 0
            in
                ( { model
                    | conversation = model.conversation ++ [ remark ]
                    , progressBar = Bar.update (Bar.Value progress) model.progressBar
                  }
                , scrollTop "#output"
                )

        SetEnemyImage src ->
            { model | enemyImage = src } ! []

        Tick newTime ->
            let
                elapsed =
                    if model.firstTick then
                        0
                    else
                        Time.inSeconds (newTime - model.clock)

                progress =
                    max (model.progressBar.value - model.drainRate * elapsed) 0

                progressBar =
                    Bar.update (Bar.Value progress) model.progressBar

                progressBar2 =
                    { progressBar
                        | sliderClasses =
                            if progress > model.overload then
                                [ "overload" ]
                            else
                                [ "normal" ]
                    }
            in
                { model
                    | clock = newTime
                    , progressBar = progressBar2
                    , firstTick = False
                }
                    ! []


showWordbankWord : Word -> Wordbank.Model -> Wordbank.Model
showWordbankWord word model =
    Wordbank.update (Wordbank.Show word) model



-- VIEW
-- the following tags the Html Msg bag coming out of model.wordbank with
-- the new type TheWordbank so it can be matched and processed by
-- this model's update function. confusingly the signature of App.map
-- has List, not Html.Html or something
-- App.map TheWordbank (Wordbank.view model.wordbank)


viewSimple : Model -> Html Msg
viewSimple model =
    let
        wordbank =
            App.map UpdateWordbank (Wordbank.view model.wordbank)

        progressBar =
            div [ class "progress-bar" ]
                [ App.map UpdateProgressBar (Bar.view model.progressBar) ]

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
                [ div [ id "convo" ] (List.map viewRemark (List.reverse model.conversation))
                , div [ id "shield" ] []
                ]
    in
        div [ id "versus-main" ]
            [ enemy
            , progressBar
            , output
            , addInput
            , wordbank
            ]


view : Model -> Html Msg
view model =
    let
        wordbank =
            App.map UpdateWordbank (Wordbank.view model.wordbank)

        statusPlayer =
            div [class "status" ] [
            div [class "name"] [ text "player"]
            ,
               div
                [ class "progress-bar" ]
                [ App.map UpdateProgressBar (Bar.view model.progressBar) ]
            ,  div [class "arrow"] [] ]

        statusEnemy = 
            div [class "status" ] [
            div [class "name"] [ text model.enemyImage ]
            ,
               div
                [ class "progress-bar" ]
                [ App.map UpdateProgressBar (Bar.view model.progressBar) ]
            ,  div [class "arrow"] [] ]



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
             img [ src model.enemyImage ] []

        player =  
            img [ src model.enemyImage ] []

        output =
            div [ id "output" ]
                [ div [ id "convo" ] (List.map viewRemarkScore (List.reverse model.conversation))
                , div [ id "shield" ] []
                ]
    in

        div [ id "versus-main" ]
            [ div [ id "top-half" ]
                [ div [class "enemy"] [statusEnemy, enemy]
                , div [class "player"] [player, statusPlayer] ]


            , div [ id "bottom-half" ] [

                div [ id "bottom-left" ]
                    [ addInput
                    , wordbank ]

                , div [id "bottom-right" ]
                 [output]
                    
                    ]     
                    ]   


viewRemarkScore : Remark -> Html.Html Msg
viewRemarkScore remark =
    div [ class "remark" ]
        [ div [ class "insult" ]
            [ div [class "insult-phrase"] [text remark.insult ]
            , div [class "insult-score"] [text <| toString remark.score] ]
        , div [ class "retort" ]
            [ div [class "retort-score"] [text <| toString remark.score] 
            , div [class "retort-phrase"] [text remark.retort ] ]
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


port askFuse : ( String, List String ) -> Cmd msg


port sendInsult : ( Word, Float ) -> Cmd msg


port scrollTop : String -> Cmd msg



-- SUBSCRIPTIONS


port setEnemyImage : (String -> msg) -> Sub msg


port newWordbank : (List Word -> msg) -> Sub msg


port suggestions : (List String -> msg) -> Sub msg


port remark : (Remark -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ suggestions Suggest
        , newWordbank NewWordbank
        , remark AddRemark
        , setEnemyImage SetEnemyImage
        , AnimationFrame.times Tick
        ]
