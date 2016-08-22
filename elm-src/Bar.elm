module Bar exposing (Model, Msg(..), init, update, view)

import Html exposing (text, div, button)
import Html.Attributes exposing (id, class, style)
import Time
import String
import AnimationFrame
import Animation exposing (Animation, animation, from, to, duration, animate, static)


-- MODEL


type alias AttributeList =
    List (Html.Attribute Msg)


type alias Model =
    { value : Float
    , duration : Time.Time
    , clock : Time.Time
    , animation :
        Animation
    , boxAttributes : AttributeList
    , sliderAttributes : AttributeList
    , horizontal : Bool
    , sliderClasses : List String
    , boxClasses : List String
    }


init : Float -> Bool -> Model
init value horizontal =
    { value = value
    , duration = 1 * Time.second
    , clock =
        0
    , boxAttributes = []
    , sliderAttributes = []
    , boxClasses = []
    , sliderClasses = []
    , animation = static value
    , horizontal = horizontal
    }



-- UPDATE


type Msg
    = ChangeValue Float
    | Tick Time.Time
    | Duration Time.Time


update : Msg -> Model -> Model
update msg model =
    case msg of
        ChangeValue value ->
            let
                newAnimation =
                    animation model.clock
                        |> from model.value
                        |> to value
                        |> duration model.duration
            in
                { model
                    | value = value
                    , animation = newAnimation
                }

        Tick newTime ->
            { model | clock = newTime }

        Duration duration ->
            { model | duration = duration }



-- VIEW


defaultBoxAttributes : AttributeList
defaultBoxAttributes =
    []


defaultBoxClasses : List String
defaultBoxClasses =
    [ "bar-box" ]


defaultSliderAttributes : AttributeList
defaultSliderAttributes =
    []


defaultSliderClasses : List String
defaultSliderClasses =
    [ "bar-slider" ]


view : Model -> Html.Html Msg
view model =
    let
        progress =
            toString ((animate model.clock model.animation) * 100) ++ "%"

        shape =
            case model.horizontal of
                True ->
                    [ ( "width", progress )
                    , ( "height", "100%" )
                    ]

                False ->
                    [ ( "width", "100%" )
                    , ( "height", progress )
                    ]

        boxClass =
            class (String.join " " (defaultBoxClasses ++ model.boxClasses))

        sliderClass =
            class (String.join " " (defaultSliderClasses ++ model.sliderClasses))
    in
        div
            (defaultBoxAttributes
                ++ model.boxAttributes
                ++ [ boxClass ]
            )
            [ div
                (defaultSliderAttributes
                    ++ [ style (shape) ]
                    ++ model.sliderAttributes
                    ++ [ sliderClass ]
                )
                []
            ]



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ AnimationFrame.times Tick
        ]
