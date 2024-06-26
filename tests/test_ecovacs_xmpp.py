from re import search

from sucks import *


# There are few tests for the XMPP stuff here because it's relatively complicated to test given
# the library's design and its multithreaded nature and lack of explicit testing support.


def test_wrap_command():
    x = make_ecovacs_xmpp()
    c = str(
        x._wrap_command(Clean().to_xml(), "E0000000001234567890@126.ecorobot.net/atom")
    )
    assert search(r'from="20170101abcdefabcdefa@ecouser.net/abcdef12"', c)
    assert search(r'to="E0000000001234567890@126.ecorobot.net/atom"', c)


def test_subscribe_to_ctls():
    response = None

    def save_response(value):
        nonlocal response
        response = value

    x = make_ecovacs_xmpp()

    query = x.make_iq_query()
    query.set_payload(
        ET.fromstring(
            '<query xmlns="com:ctl"><ctl td="CleanReport"> <clean type="auto" /> </ctl></query>'
        )
    )

    x.subscribe_to_ctls(save_response)
    x._handle_ctl(query)
    assert response == {"event": "clean_report", "type": "auto"}


def test_xml_to_dict():
    x = make_ecovacs_xmpp()

    assert x._ctl_to_dict(
        make_ctl('<ctl td="CleanReport"> <clean type="auto" /> </ctl>')
    ) == {"event": "clean_report", "type": "auto"}
    assert x._ctl_to_dict(
        make_ctl('<ctl td="CleanReport"> <clean type="auto" speed="strong" /> </ctl>')
    ) == {"event": "clean_report", "type": "auto", "speed": "strong"}

    assert x._ctl_to_dict(
        make_ctl('<ctl td="BatteryInfo"><battery power="095"/></ctl>')
    ) == {"event": "battery_info", "power": "095"}

    assert x._ctl_to_dict(
        make_ctl('# <ctl td="LifeSpan" type="Brush" val="099" total="365"/>')
    ) == {"event": "life_span", "type": "brush", "val": "099", "total": "365"}


def make_ecovacs_xmpp():
    return EcoVacsXMPP(
        "20170101abcdefabcdefa",
        "ecouser.net",
        "abcdef12",
        "A1b2C3d4efghijklmNOPQrstuvwxyz12",
        "na",
    )


def make_ctl(string):
    return ET.fromstring('<query xmlns="com:ctl">' + string + "</query>")[0]
