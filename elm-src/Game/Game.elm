port module Game.Game exposing (..)

import Loadout.Loadout as Loadout
import Versus.Versus as Versus
import Versus.Types exposing (Player, Enemy)
import Game.View exposing (view)
import Game.Types exposing (..)
import Map.Map as Map
import Map.Types
import Menu.Menu as Menu
import Menu.Types
import Html.App as App
import Keyboard
import Char


main : Program Never
main =
    App.program
        { init = init testPlayer testEnemy testMap
        , update = update
        , view = view
        , subscriptions = subscriptions
        }


init : Player -> Enemy -> Map.Types.Map -> ( Model, Cmd Msg )
init player enemy map =
    let

        model =
            { menu = initMenu
            , loadout = initLoadout player
            , versus = initVersus player enemy 
            , map = Map.init Map.testMap
            , loadoutStatus = Active
            , menuStatus = Hidden
            , mapStatus = Hidden
            , versusStatus = Hidden
            , player = player
            }
    in
        model ! []

testPlayer : Player
testPlayer =
    { loaded = testWords1, unloaded = testWords2, capacity = testCapacity, health = 1, image = "", name = "player" }

testWords1 : List { partOfSpeech : String, tag : String, word : String }
testWords1 = [{ word = "Test", partOfSpeech = "1", tag = "whatevs"},
              { word = "Another Test", partOfSpeech = "1", tag = "asdf"},
              { word = "ABC", partOfSpeech = "2", tag = "alphabet"} ]

testWords2 : List { partOfSpeech : String, tag : String, word : String }
testWords2 = [{ word = "Unloaded", partOfSpeech = "2", tag = "asdf"}]

testCapacity : List ( String, number )
testCapacity = [("2", 2), ("1", 1)]

testEnemy : Enemy
testEnemy = 
    { image = "static/images/ctenophora.png", name = "test", health = 1}

testMap : Map.Types.Map
testMap = 
    Map.testMap



initMenu : Menu.Types.Model
initMenu =
    Menu.init tiles "my-menu"


initLoadout : Player -> Loadout.Model
initLoadout player =
    Loadout.init player.loaded player.unloaded player.capacity



initVersus : Player -> Enemy -> Versus.Types.Model
initVersus player enemy = 
    let 
        maxToDisplay =
            30
        words =
            []
    in
        fst (Versus.init words player enemy maxToDisplay)





tiles : List Menu.Types.Tile
tiles =
    [ { label = ": loadout", key = 'l',  x = 0, y = 0 }
    ]



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateVersus msg ->
            let
                ( newversus, newMsg ) =
                    Versus.update msg model.versus

                newModel =
                    { model | versus = newversus }
            in
                case model.versusStatus of 
                    Active ->
                        ( newModel, Cmd.map UpdateVersus newMsg )
                    _ -> 
                        model ! []

        UpdateLoadout msg ->

             case model.loadoutStatus of
                    Active ->

                        let
                            ( newLoadout, newMsg ) =
                                Loadout.update msg model.loadout

                            newModel =
                                { model | loadout = newLoadout }

                            player =
                                newModel.player

                            newPlayer =
                                { player | loaded = newLoadout.loaded, unloaded = newLoadout.unloaded }

                            ( newModel2, newMsg2 ) =
                                update (SetPlayer newPlayer) newModel

                            cmds =
                                Cmd.batch
                                    [ Cmd.map UpdateLoadout newMsg
                                    , newMsg2
                                    ]
                        in
                           
                                    ( newModel2, cmds )
                    _ -> 
                        model ! []


        UpdateMenu msg ->

                model ! []

        UpdateMap msg ->

                let
                    ( newMap, _, selection ) =
                        Map.update msg model.map

                in
                    case selection of
                        Just label ->
                            ( model , sendTransition label)

                        Nothing ->
                            { model | map = newMap } ! []

                        


        SetMap map ->
           { model | map = Map.init map } ! []

        SetVersus versus ->
            let
                newVersus =
                    initVersus model.player versus
            in
                {model | versus = newVersus} ! []

        SetPlayer player ->
            {model | player = player} ! []


        KeyPress key ->
            if key == (Char.toCode ':') || key == (Char.toCode ';') then

                case model.loadoutStatus of
                    Active ->
                        { model | loadoutStatus = Hidden } ! []
                    _ ->
                        { model | loadoutStatus = Active } ! []
            else
                model ! []

        NoOp ->
            model ! []




--OUTGOING


port sendLoadout : Player -> Cmd msg


port sendTransition: String -> Cmd msg


port setFocus : String -> Cmd msg



-- INCOMING


port setMap : (Map.Types.Map -> msg) -> Sub msg


port setPlayer : (Player -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        , Sub.map UpdateLoadout (Loadout.subscriptions model.loadout)
        , Sub.map UpdateVersus (Versus.subscriptions model.versus)
        , Sub.map UpdateMap (Map.subscriptions model.map)
        , Keyboard.presses KeyPress
        , setMap SetMap
        , setPlayer SetPlayer
        ]


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
