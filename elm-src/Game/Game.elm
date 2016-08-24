port module Game.Game exposing (..)

import Loadout.Loadout as Loadout
import Versus.Versus as Versus exposing (testPlayer, testEnemy)
import Versus.Types exposing (Player, Enemy)
import Game.View exposing (view)
import Game.Types exposing (..)
import Message.Message as Message
import Map.Map as Map
import Map.Types
import Menu.Menu as Menu
import Menu.Types
import Html.App as App
import Keyboard
import Char
import Debug


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
            , message = Message.initDummy
            , loadoutStatus = Hidden
            , menuStatus = Active
            , mapStatus = Hidden
            , versusStatus = Hidden
            , messageStatus = Hidden
            , player = player
            }
    in
        model ! []


initMenu : Menu.Types.Model
initMenu =
    Menu.init tiles "options"


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
    [ { label = ": loadout", key = 'l', x = 0, y = 0 }
    ]



-- TEST




testMap : Map.Types.Map
testMap =
    Map.testMap



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateVersus msg ->
            case model.versusStatus of
                Active ->
                    let
                        ( newversus, newMsg ) =
                            Versus.update msg model.versus

                        newModel =
                            { model | versus = newversus }
                    in
                        
                                ( newModel, Cmd.map UpdateVersus newMsg )

                _ ->
                    model ! []

        UpdateLoadout msg ->
            case model.loadoutStatus of
                Active ->
                    let
                        -- update model.loadout, then model.player

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
                                , sendLoadout newModel2.player
                                ]
                    in
                        ( newModel2, cmds )

                _ ->
                    model ! []

        UpdateMenu msg ->
            case model.menuStatus of
                Active ->
                    let
                        ( newMenu, selected ) =
                            Menu.update msg model.menu
                    in
                        case selected of
                            Just 'l' ->
                                {model | menu = newMenu
                                       , loadoutStatus = Active
                                       , mapStatus = Inactive
                                       , menuStatus = Hidden
                                       , versusStatus = Hidden
                                       , loadout = initLoadout model.player} ! []
                            _ ->
                                { model | menu = newMenu } ! []
                        

                _ ->
                    model ! []

        UpdateMap msg ->
            let
                ( newMap, _, selection ) =
                    Map.update msg model.map
            in
                case selection of
                    Just label ->
                        let 
                            logger = Debug.log "sent transition" label
                        in
                            ( model, sendTransition label )

                    Nothing ->
                        { model | map = newMap } ! []

        UpdateMessage msg ->
            let
                (newMessage, selection) = 
                    Message.update msg model.message
            in
                case selection of
                    Just label ->
                        let 
                            logger = Debug.log "sent transition" label
                        in
                            ( model, sendTransition label )
                    Nothing ->
                        { model | message = newMessage} ! []

        SetMap map ->
            { model 
            | map = Map.init map
            , mapStatus = Active
            , menuStatus = Hidden
            , versusStatus = Hidden
            , loadoutStatus = Hidden } ! []

        SetMessage message ->
            { model
            | message = Message.init message
            , messageStatus = Active
            , mapStatus = Inactive
            , menuStatus = Hidden
            , versusStatus = Hidden
            , loadoutStatus = Hidden
            } ! []

        SetVersus versus ->
            let
                newVersus =
                    initVersus model.player versus

                logger = Debug.log "SetVersus" versus
                --logger2 = Debug.log "Player is" model.player

                logger3 = Debug.log "newVersus.wordbank.words is" newVersus.wordbank.words
            in
                { model | versus = newVersus
                , mapStatus = Inactive
                , menuStatus = Hidden
                , versusStatus = Active
                , loadoutStatus = Hidden } ! []

        SetPlayer player ->
            { model | player = player } ! []

        KeyPress key ->
            let
                keyFlag =
                    key == (Char.toCode ':') || key == (Char.toCode ';')

                stateFlag =
                    model.versusStatus == Hidden
            in
                if keyFlag then
                    case model.menuStatus of
                        Active ->
                            { model
                                | loadoutStatus = Hidden
                                , mapStatus = Active
                                , menuStatus = Hidden
                                , versusStatus = Hidden
                            }
                                ! []

                        _ ->
                            case model.versusStatus of 
                                Active ->
                                    { model
                                        | loadoutStatus = Hidden
                                        , mapStatus = Active
                                        , menuStatus = Hidden
                                        , versusStatus = Hidden
                                    }
                                        ! []
                                _ ->
                                    { model
                                        | loadoutStatus = Hidden
                                        , mapStatus = Inactive
                                        , menuStatus = Active
                                        , versusStatus = Hidden
                                    }
                                        ! []
                else
                    model ! []

        NoOp ->
            model ! []



--OUTGOING


port sendLoadout : Player -> Cmd msg


port sendTransition : String -> Cmd msg


port setFocus : String -> Cmd msg



-- INCOMING


port setMap : (Map.Types.Map -> msg) -> Sub msg

port setMessage : (Message.Message -> msg) -> Sub msg

port setEncounter : (Enemy -> msg) -> Sub msg



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
        , setEncounter SetVersus
        , setMessage SetMessage
        ]


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
