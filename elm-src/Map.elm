port module Map exposing (..)

import Loadout.Loadout as Loadout
import Versus
import View exposing (..)
import Types exposing (..)
import Menu.Menu as Menu
import Menu.Types
import Html.App as App
import Keyboard
import Char
import String


main : Program Never
main =
    App.program
        { init = init
        , update = update
        , view = view
        , subscriptions = subscriptions
        }


init : ( Model, Cmd Msg )
init =
    let
        player =
            { loaded = [], unloaded = [], capacity = [] }

        model =
            { menu = initMenu
            , loadout = initLoadout player
            , encounter = initEncounter
            , weapons = initWeapons
            , mapMenu = initMapMenu
            , map = { image = "", places = [] }
            , overlay = NoOverlay
            , key = keycode.enter
            , player = player
            }
    in
        update NoOp model


initMenu : Menu.Types.Model
initMenu =
    Menu.init tiles "my-menu"


initWeapons : Menu.Types.Model
initWeapons =
    Menu.init tilesWeapons "my-menu"


initLoadoutLongform : List ( String, String, Bool ) -> Loadout.Model
initLoadoutLongform longform =
    Loadout.initFromLongform longform


initLoadout : Player -> Loadout.Model
initLoadout player =
    Loadout.init player.loaded player.unloaded player.capacity


initEncounter : Versus.Model
initEncounter =
    let
        words =
            []

        enemyImage =
            ""

        maxToDisplay =
            30
    in
        fst (Versus.init words enemyImage maxToDisplay)


initMapMenu : Menu.Types.Model
initMapMenu =
    Menu.init [] ""


tiles : List Menu.Types.Tile
tiles =
    [ { label = ": loadout", key = 'l', id = "loadout", x = 0, y = 0 }
    , { label = ": encounter", key = 'e', id = "e", x = 0, y = 0 }
    , { label = ": weapons", key = 'w', id = "w", x = 0, y = 0 }
    ]


tilesWeapons : List Menu.Types.Tile
tilesWeapons =
    [ { label = ": gun", key = 'g', id = "gun", x = 0, y = 0 }
    , { label = ": knife", key = 'k', id = "knife", x = 0, y = 0 }
    ]


ccc : List ( String, String, Bool )
ccc =
    [ ( "Adjective", "Fuckers", False )
    , ( "Noun", "You", False )
    , ( "Adjective", "Hello", True )
    , ( "Noun", "There", True )
    , ( "Noun", "Asshat", True )
    , ( "Noun", "There2", True )
    , ( "Noun", "Asshat2", True )
    , ( "Noun", "There3", True )
    , ( "Noun", "Asshat3", True )
    ]



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateEncounter msg ->
            let
                ( newEncounter, newMsg ) =
                    Versus.update msg model.encounter

                newModel =
                    { model | encounter = newEncounter }
            in
                ( newModel, Cmd.map UpdateEncounter newMsg )

        --update (AskSuggestions input) { model | addInput = input }
        UpdateLoadout msg ->
            if model.overlay /= LoadoutOverlay then
                model ! []
            else
                let
                    ( newLoadout, newMsg ) =
                        Loadout.update msg model.loadout

                    newModel = { model | loadout = newLoadout }

                    player = newModel.player

                    newPlayer = {player | loaded = newLoadout.loaded, unloaded = newLoadout.unloaded}

                    (newModel2, newMsg2) = update (SetPlayer newPlayer) newModel
                    
                    cmds = Cmd.batch [Cmd.map UpdateLoadout newMsg,
                                        newMsg2]
                in
                    (newModel2, cmds)

        UpdateWeapons msg ->
            if model.overlay /= WeaponsOverlay then
                model ! []
            else
                let
                    ( newWeapons, selection ) =
                        Menu.update msg model.weapons
                in
                    case selection of
                        Nothing ->
                            { model | weapons = newWeapons } ! []

                        _ ->
                            update (ChangeOverlay NoOverlay) { model | weapons = newWeapons }

        UpdateMenu msg ->
            if model.overlay /= MenuOverlay then
                model ! []
            else
                let
                    ( newMenu, selection ) =
                        Menu.update msg model.menu
                in
                    case selection of
                        Nothing ->
                            { model | menu = newMenu } ! []

                        Just 'l' ->
                            update (ChangeOverlay LoadoutOverlay) model

                        Just 'w' ->
                            update (ChangeOverlay WeaponsOverlay) model

                        Just 'e' ->
                            update (ChangeOverlay (EncounterOverlay 'e')) model

                        _ ->
                            update (ChangeOverlay NoOverlay) { model | menu = newMenu }

        UpdateMapMenu msg ->
            if model.overlay /= NoOverlay then
                model ! []
            else
                let
                    ( newMapMenu, selection ) =
                        Menu.update msg model.mapMenu
                in
                    case selection of
                        Nothing ->
                            { model | mapMenu = newMapMenu } ! []

                        Just char ->
                            update (ChangeOverlay (EncounterOverlay char)) model

        ChangeOverlay overlay ->
            case overlay of
                NoOverlay ->
                    { model | overlay = overlay } ! []

                EncounterOverlay char ->
                    let
                        place =
                            model.map.places
                                |>
                                    List.filter (\p -> p.label == (String.fromChar char))
                                -- matches char
                                |>
                                    List.head
                    in
                        case place of
                            Nothing ->
                                model ! []

                            Just p ->
                                ( { model
                                    | overlay = overlay
                                    , encounter = initEncounter
                                  }
                                , Cmd.batch [ requestEncounter ( p.enemy, model.player ), setFocus Versus.inputID ]
                                )

                LoadoutOverlay ->
                    { model
                        | overlay = overlay
                        , loadout = initLoadout model.player
                    }
                        ! []

                WeaponsOverlay ->
                    { model
                        | overlay = overlay
                        , weapons = initWeapons
                    }
                        ! []

                MenuOverlay ->
                    { model
                        | overlay = overlay
                        , menu = initMenu
                    }
                        ! []

        KeyPress key ->
            if key == (Char.toCode ':') || key == (Char.toCode ';') then
                case model.overlay of
                    NoOverlay ->
                        { model | overlay = MenuOverlay, key = key, menu = initMenu } ! []

                    _ ->
                        update (SetMap model.map) { model | overlay = NoOverlay, key = key }
            else
                { model | key = key } ! []

        SetMap map ->
            let
                placeToLabel place =
                    let
                        key =
                            case String.uncons place.label of
                                Just ( char, _ ) ->
                                    char

                                Nothing ->
                                    '.'
                    in
                        { label = place.enemy
                        , key = key
                        , id = place.label
                        , x = place.x
                        , y = place.y
                        }

                tiles =
                    List.map placeToLabel map.places

                mapMenu =
                    Menu.init tiles "map-menu"
            in
                { model | map = map, mapMenu = mapMenu } ! []

        SetPlayer player ->
            { model | player = player } ! []

        NoOp ->
            model ! []



--OUTGOING


port updatePlayer : Player -> Cmd msg


port requestEncounter : ( String, Player ) -> Cmd msg


port setFocus : String -> Cmd msg



-- INCOMING


port setMap : (Map -> msg) -> Sub msg


port setPlayer : (Player -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        , Sub.map UpdateWeapons (Menu.subscriptions model.weapons)
        , Sub.map UpdateLoadout (Loadout.subscriptions model.loadout)
        , Sub.map UpdateEncounter (Versus.subscriptions model.encounter)
        , Sub.map UpdateMapMenu (Menu.subscriptions model.mapMenu)
        , Keyboard.presses KeyPress
        , setMap SetMap
        , setPlayer SetPlayer
        ]


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
