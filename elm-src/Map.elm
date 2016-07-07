port module Map exposing (..)

import Versus
import View exposing (..)
import Model exposing (..)
import Menu.Menu as Menu
import Menu.Types
import Menu.View
import Html.App as App
import Keyboard
import Char


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
        model =
            { menu = initMenu
            , loadout = initLoadout
            , encounter = initEncounter
            , map = { image = "", places = [] }
            , overlay = NoOverlay
            , key = keycode.enter
            }
    in
        update NoOp model


initMenu : Menu.Types.Model
initMenu =
    Menu.init tiles "my-menu"


initLoadout : Menu.Types.Model
initLoadout =
    Menu.init tilesL "my-loadout"


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


tiles : List Menu.Types.Tile
tiles =
    [ { label = ": loadout", key = 'l', id = "loadout" }
    , { label = ": encounter", key = 'e', id = "e" }
    ]


tilesL : List Menu.Types.Tile
tilesL =
    [ { label = ": gun", key = 'g', id = "gun" }
    , { label = ": knife", key = 'k', id = "knife" }
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
                    ( newLoadout, selection ) =
                        Menu.update msg model.loadout
                in
                    case selection of
                        Nothing ->
                            { model | loadout = newLoadout } ! []

                        _ ->
                            update (ChangeOverlay NoOverlay) { model | loadout = newLoadout }

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

                        Just 'e' ->
                            update (ChangeOverlay EncounterOverlay) model

                        _ ->
                            update (ChangeOverlay NoOverlay) { model | menu = newMenu }

        ChangeOverlay overlay ->
            case overlay of
                NoOverlay ->
                    { model | overlay = overlay } ! []

                EncounterOverlay ->
                    { model
                        | overlay = overlay
                        , encounter = initEncounter
                    }
                        ! [ requestEncounter "base" ]

                LoadoutOverlay ->
                    { model
                        | overlay = overlay
                        , loadout = initLoadout
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
                    EncounterOverlay ->
                        { model | overlay = NoOverlay, key = key } ! []

                    NoOverlay ->
                        { model | overlay = MenuOverlay, key = key, menu = initMenu } ! []

                    _ ->
                        { model | key = key } ! []
            else
                { model | key = key } ! []

        SetMap map ->
            { model | map = map } ! []

        NoOp ->
            model ! []



--OUTGOING


port requestEncounter : String -> Cmd msg



-- INCOMING


port setMap : (Map -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        , Sub.map UpdateLoadout (Menu.subscriptions model.loadout)
        , Sub.map UpdateEncounter (Versus.subscriptions model.encounter)
        , Keyboard.presses KeyPress
        , setMap SetMap
        ]


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
