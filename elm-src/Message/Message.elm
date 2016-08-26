module Message.Message exposing (Model, Msg, init, 
                                 initDummy, update, view, 
                                 Message, subscriptions)

import Menu.Menu as Menu
import Menu.Types exposing (keycode, Tile)
import Menu.View exposing (view)
import Html exposing (text, div, Html)
import Html.Attributes exposing (id, class)
import Markdown
import String
import Html.App as App


--main : Program Never
--main =
--    App.program
--        { init = init [] "" 30
--        , update = update
--        , view = view
--        , subscriptions = subscriptions
--        }
-- MODEL


type alias Model =
    { text : String
    , menu : Menu.Types.Model
    , name : String
    , choices : List Choice
    , isSplash : Bool
    }


type alias Message =
    { text : String
    , choices : List Choice
    , name : String
    }


type alias Choice =
    { label : String
    , key : String
    , name : String
    }


init : Message -> Model
init message =
    let
        tiles =
            List.map choiceToTile message.choices

        id =
            "message-menu"

        isSplash = tiles |> List.filter (\t->t.key == '*')
                         |> List.isEmpty
                         |> not
    in
        { text = message.text
        , menu = Menu.init tiles id
        , name = message.name
        , choices = message.choices
        , isSplash = isSplash
        }


initDummy : Model
initDummy =
    { text = "dummy-message-text"
    , menu = Menu.init [] ""
    , name = "dummy-message"
    , choices = []
    , isSplash = False
    }


choiceToTile : Choice -> Tile
choiceToTile choice =
    let
        key =
            String.uncons choice.key
                |> Maybe.withDefault ( ' ', "" )
                |> fst
    in
        { label = choice.label
        , key = key
        , x = 0
        , y = 0
        }



-- UPDATE


type Msg
    = UpdateMenu Menu.Types.Msg


update : Msg -> Model -> ( Model, Maybe String )
update msg model =
    case msg of
        UpdateMenu msg ->
            let
                ( newMenu, selection ) =
                    Menu.update msg model.menu

                newModel =
                    { model | menu = newMenu }

                getLabel c =
                    List.filter (\tile -> tile.key == c) model.menu.tiles
                        |> List.map .label
                        |> List.head

                getName label = 
                    List.filter (\choice -> choice.label == label) model.choices
                        |> List.map .name
                        |> List.head

            in
                if model.isSplash then
                    let
                        name =  List.head model.choices |> Maybe.map .name
                    in
                        (newModel , name )
                else
                    case selection of
                        Nothing ->
                            ( newModel, Nothing )

                        Just char ->
                            let
                                name = (getLabel char) `Maybe.andThen` getName
                            in
                                ( newModel, name )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Sub.map UpdateMenu (Menu.subscriptions model.menu)
        ]



-- VIEW


view : Model -> Html Msg
view model =
    let 
        choices = if model.isSplash then
                        div [] []
                  else 
                        App.map UpdateMenu (Menu.View.view model.menu)
    in
        div [ class "message" ] [ Markdown.toHtml [class "markdown"] model.text, choices ]
