from unittest.mock import Mock
from sleekxmppfs.exceptions import XMPPError

from sucks import *


def test_handle_clean_report():
    v = a_vacbot()
    assert v.clean_status == None

    v._handle_ctl({"event": "clean_report", "type": "auto", "speed": "strong"})
    assert v.clean_status == "auto"
    assert v.fan_speed == "high"

    v._handle_ctl({"event": "clean_report", "type": "border", "speed": "standard"})
    assert v.clean_status == "edge"
    assert v.fan_speed == "normal"

    # Missing fan_speed
    v = a_vacbot()
    v._handle_ctl({"event": "clean_report", "type": "border"})
    assert v.clean_status == "edge"
    assert v.fan_speed == None

    # For states not handled by sucks constants, fall back to just using whatever the vacuum said
    v._handle_ctl(
        {
            "event": "clean_report",
            "type": "a_type_not_supported_by_sucks",
            "speed": "a_weird_speed",
        }
    )
    assert v.clean_status == "a_type_not_supported_by_sucks"
    assert v.fan_speed == "a_weird_speed"


def test_handle_charge_state():
    v = a_vacbot()
    assert v.clean_status == None

    v._handle_ctl({"event": "charge_state", "type": "going"})
    assert v.charge_status == "returning"

    v._handle_ctl({"event": "charge_state", "type": "slot_charging"})
    assert v.charge_status == "charging"

    v._handle_ctl({"event": "charge_state", "type": "idle"})
    assert v.charge_status == "idle"

    v._handle_ctl({"event": "charge_state", "type": "a_type_not_supported_by_sucks"})
    assert v.charge_status == "a_type_not_supported_by_sucks"


def test_vacuum_states():
    # Vacuum state usually mirrors the latest charge or clean report, but there are some edge cases where it doesn't
    # work that way. This test ensures the edge cases are handled correctly.
    v = a_vacbot()
    assert v.vacuum_status == None

    v._handle_ctl({"event": "clean_report", "type": "auto", "speed": "strong"})
    assert v.vacuum_status == "auto"

    # Ignore the "idle" charge state in most cases, as it can be reported during a cleaning (such as during initialization)
    v._handle_ctl({"event": "clean_report", "type": "auto"})
    v._handle_ctl({"event": "charge_state", "type": "idle"})
    assert v.vacuum_status == "auto"

    # However, we do honor the idle state when our current state is charging, as that can happen in some certain combination of events
    v._handle_ctl({"event": "charge_state", "type": "slot_charging"})
    v._handle_ctl({"event": "charge_state", "type": "idle"})
    assert v.vacuum_status == "idle"


def test_handle_battery_info():
    v = a_vacbot()
    assert v.battery_status == None

    v._handle_ctl({"event": "battery_info", "power": "100"})
    assert v.battery_status == 1.0

    v._handle_ctl({"event": "battery_info", "power": "095"})
    assert v.battery_status == 0.95

    v._handle_ctl({"event": "battery_info", "power": "000"})
    assert v.battery_status == 0.0


def test_lifespan_reports():
    v = a_vacbot()
    assert v.components == {}

    # Note: The "total" values don't seem to have any meaning

    v._handle_ctl(
        {"event": "life_span", "type": "side_brush", "total": "100", "val": "50"}
    )
    assert v.components == {"side_brush": 0.5}

    v._handle_ctl({"event": "life_span", "type": "brush", "total": "200", "val": "1"})
    assert v.components == {"side_brush": 0.5, "main_brush": 0.01}

    v._handle_ctl(
        {"event": "life_span", "type": "side_brush", "total": "100", "val": "0"}
    )
    assert v.components == {"side_brush": 0, "main_brush": 0.01}

    v._handle_ctl(
        {"event": "life_span", "type": "a_weird_component", "total": "100", "val": "87"}
    )
    assert v.components == {
        "side_brush": 0,
        "main_brush": 0.01,
        "a_weird_component": 0.87,
    }


def test_is_cleaning():
    v = a_vacbot()

    assert not v.is_cleaning

    v._handle_ctl({"event": "clean_report", "type": "auto", "speed": "strong"})
    assert v.is_cleaning

    v._handle_ctl({"event": "clean_report", "type": "stop"})
    assert not v.is_cleaning

    v._handle_ctl({"event": "clean_report", "type": "edge", "speed": "normal"})
    assert v.is_cleaning

    v._handle_ctl({"event": "charge_state", "type": "going"})
    assert not v.is_cleaning


def test_is_charging():
    v = a_vacbot()

    assert not v.is_charging

    v._handle_ctl({"event": "clean_report", "type": "auto", "speed": "strong"})
    assert not v.is_charging

    v._handle_ctl({"event": "charge_state", "type": "going"})
    assert not v.is_charging

    v._handle_ctl({"event": "charge_state", "type": "slot_charging"})
    assert v.is_charging

    v._handle_ctl({"event": "clean_report", "type": "edge", "speed": "normal"})
    assert not v.is_charging


def test_send_ping_no_monitor():
    v = a_vacbot()

    mock = v.xmpp.send_ping = Mock()
    v.send_ping()

    # On four failed pings, vacuum state gets set to 'offline'
    mock.side_effect = XMPPError()
    v.send_ping()
    v.send_ping()
    v.send_ping()
    assert v.vacuum_status == None
    v.send_ping()
    assert v.vacuum_status == "offline"

    # On a successful ping after the offline state, state gets reset to None, indicating that it is unknown
    mock.side_effect = None
    v.send_ping()
    assert v.vacuum_status == None


def test_send_ping_with_monitor():
    v = a_vacbot(monitor=True)

    ping_mock = v.xmpp.send_ping = Mock()
    request_statuses_mock = v.request_all_statuses = Mock()

    # First ping should try to fetch statuses
    v.send_ping()
    assert request_statuses_mock.call_count == 1

    # Nothing blowing up is success

    # On four failed pings, vacuum state gets set to 'offline'
    ping_mock.side_effect = XMPPError()
    v.send_ping()
    v.send_ping()
    v.send_ping()
    assert v.vacuum_status == None
    v.send_ping()
    assert v.vacuum_status == "offline"

    # On a successful ping after the offline state, a request for initial statuses is made
    ping_mock.side_effect = None
    request_statuses_mock.reset_mock()
    v.send_ping()
    assert request_statuses_mock.call_count == 1


def test_status_event_subscription():
    v = a_vacbot()

    mock = Mock()
    v.statusEvents.subscribe(mock)
    v._handle_ctl({"event": "clean_report", "type": "auto", "speed": "strong"})
    mock.assert_called_once_with("auto")

    mock = Mock()
    v.statusEvents.subscribe(mock)
    v._handle_ctl({"event": "charge_state", "type": "going"})
    mock.assert_called_once_with("returning")

    # Test unsubscribe
    mock = Mock()
    subscription = v.statusEvents.subscribe(mock)
    v._handle_ctl({"event": "charge_state", "type": "going"})
    assert mock.call_count == 1

    subscription.unsubscribe()
    v._handle_ctl({"event": "charge_state", "type": "slot_charging"})
    assert mock.call_count == 1


def test_battery_event_subscription():
    v = a_vacbot()

    mock = Mock()
    v.batteryEvents.subscribe(mock)
    v._handle_ctl({"event": "battery_info", "power": "095"})
    mock.assert_called_once_with(0.95)

    # Test unsubscribe
    mock = Mock()
    subscription = v.batteryEvents.subscribe(mock)
    v._handle_ctl({"event": "battery_info", "power": "095"})
    assert mock.call_count == 1

    subscription.unsubscribe()
    v._handle_ctl({"event": "battery_info", "power": "090"})
    assert mock.call_count == 1


def test_lifespan_event_subscription():
    v = a_vacbot()

    mock = Mock()
    v.lifespanEvents.subscribe(mock)
    v._handle_ctl(
        {"event": "life_span", "type": "side_brush", "total": "100", "val": "50"}
    )
    mock.assert_called_once_with({"type": "side_brush", "lifespan": 0.5})

    # Test unsubscribe
    mock = Mock()
    subscription = v.lifespanEvents.subscribe(mock)
    v._handle_ctl(
        {"event": "life_span", "type": "side_brush", "total": "100", "val": "50"}
    )
    assert mock.call_count == 1

    subscription.unsubscribe()
    v._handle_ctl(
        {"event": "life_span", "type": "side_brush", "total": "100", "val": "25"}
    )
    assert mock.call_count == 1


def test_error_event_subscription():
    v = a_vacbot()

    mock = Mock()
    v.errorEvents.subscribe(mock)
    v._handle_ctl({"event": "error", "error": "an_error_name"})
    mock.assert_called_once_with("an_error_name")

    for err_code, err_msg in ERROR_CODES.items():
        v._handle_ctl({"event": "error", "errno": err_code})
        mock.assert_called_with(err_msg)

    v._handle_ctl({"event": "error", "errno": "999"})
    mock.assert_called_with("unknown")

    v._handle_ctl({"event": "error"})
    mock.assert_called_with("unknown")

    # Test unsubscribe
    mock = Mock()
    subscription = v.errorEvents.subscribe(mock)
    v._handle_ctl({"event": "error", "error": "an_error_name"})
    assert mock.call_count == 1

    subscription.unsubscribe()
    v._handle_ctl({"event": "error", "error": "an_error_name"})
    assert mock.call_count == 1


def test_handle_unknown_ctl():
    v = a_vacbot()
    v._handle_ctl({"event": "weird_and_unknown_event", "type": "pretty_weird"})
    # as long as it doesn't blow up, that's fine


# as-yet unhandled messages:
#
# <ctl td="LifeSpan" type="Brush" val="099" total="365"/>
# <ctl td="LifeSpan" type="DustCaseHeap" val="098" total="365"/>
# <ctl td="LifeSpan" type="SideBrush" val="098" total="365"/>
# <ctl td="Sched2"/>
# <ctl td="Sched2" id="30800321"/>
#
# plus errors!


def test_bot_address():
    v = a_vacbot(bot={"did": "E0000000001234567890", "class": "126", "nick": "bob"})
    assert v._vacuum_address() == "E0000000001234567890@126.ecorobot.net/atom"


def test_model_variation():
    v = a_vacbot(bot={"did": "E0000000001234567890", "class": "141", "nick": "bob"})
    assert v._vacuum_address() == "E0000000001234567890@141.ecorobot.net/atom"


def a_vacbot(bot=None, monitor=False):
    if bot is None:
        bot = {"did": "E0000000001234567890", "class": "126", "nick": "bob"}
    return VacBot(
        "20170101abcdefabcdefa",
        "ecouser.net",
        "abcdef12",
        "A1b2C3d4efghijklmNOPQrstuvwxyz12",
        bot,
        "na",
        monitor=monitor,
    )
