port module Map exposing (..)

import Versus
import View exposing (..)
import Model exposing (..)
import Menu
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
            , image = "un"
            , overlay = NoOverlay
            , key = keycode.enter
            }
    in
        update NoOp model


initMenu : Menu.Model
initMenu =
    Menu.init tiles "my-menu"


initLoadout : Menu.Model
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


tiles : List Menu.Tile
tiles =
    [ { label = ": loadout", key = 'l', id = "loadout" }
    , { label = ": btw", key = 'b', id = "btw" }
    ]


tilesL : List Menu.Tile
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
                    { model | loadout = newLoadout } ! []

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

                        Just 'b' ->
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
            if key == (Char.toCode ':') then
                { model | overlay = MenuOverlay, key = key, menu = initMenu } ! []
            else if key == keycode.space then
                { model | overlay = NoOverlay, key = key } ! []
            else
                { model | key = key } ! []

        SetMapImage image ->
            { model | image = image } ! []

        NoOp ->
            model ! []



--OUTGOING


port requestEncounter : String -> Cmd msg



-- INCOMING


port setMapImage : (String -> msg) -> Sub msg


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        , Sub.map UpdateLoadout (Menu.subscriptions model.loadout)
        , Sub.map UpdateEncounter (Versus.subscriptions model.encounter)
        , Keyboard.presses KeyPress
        , setMapImage SetMapImage
        ]


keycode : { escape : Int, shift : Int, space : Int, enter : Int }
keycode =
    { enter = 13, shift = 16, space = 32, escape = 27 }
