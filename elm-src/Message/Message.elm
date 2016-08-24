module Message.Message exposing (Model, Msg(..), init, initDummy, update, view, Message)

import Menu.Menu as Menu
import Menu.Types exposing (keycode, Tile)
import Html exposing (text, div, Html)
import Html.Attributes exposing (id, class)
import Html.App as App
import Markdown
import String

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
    , class : String
    }

type alias Message = 
    { text : String
    , choices : List Choice
    , class : String
    }

type alias Choice = 
    { label : String
    , key : String
    }


init : Message -> Model
init message =
    let 
        tiles = List.map choiceToTile message.choices

        id = "message"

    in
        { text = message.text
        , menu = Menu.init tiles id 
        , class = message.class
        }

initDummy : Model
initDummy = 
    { text = "dummy"
    , menu = Menu.init [] ""
    , class = ""
    }


choiceToTile : Choice -> Tile
choiceToTile choice = 
    let
        key = String.uncons choice.key
              |> Maybe.withDefault (' ', "")
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


update : Msg -> Model -> (Model, Maybe String)
update msg model =
    case msg of
        UpdateMenu msg ->
            let
                ( newMenu, selection ) =
                    Menu.update msg model.menu
                newModel = 
                    { model | menu = newMenu }
            in
                case selection of
                    Nothing ->
                        (newModel, Nothing)

                    Just char ->
                        let 
                            label = List.filter (\tile -> tile.key == char) model.menu.tiles
                                            |> List.map .label
                                            |> List.head
                        in 
                            (newModel, label)



subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch [
         Sub.map UpdateMenu (Menu.subscriptions model.menu)
        ]

-- VIEW


view : Model -> Html Msg
view model =
    div [ class ("message " ++ model.class) ] [ Markdown.toHtml [] model.text ]
