# Development resources and information for Ecovacs Robot Vacuums

For a description of the Ecovacs API protocols, see
[the protocol documentation](protocol.md)

## Getting started with Sucks

If you'd like to join in on developing, I recommend checking out the code,
[setting up a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/),
and installing this package in dev mode. You can confirm your environment
works by running the tests. The commands for that look something like
like

```bash
python3 -m virtualenv env
source env/bin/activate
pip install -e .[dev]
pytest tests
```

If the test run is successful, it will say something like

```
44 passed in 0.16s
```

Current test are not yet
comprehensive, as the integrated nature of this makes it difficult.
But we aim to reduce that problem over time, so please add tests as you go.

## MITM XMPP traffic between the Android or iOS App and the Ecovacs server

1. Download [xmpppeek](https://www.beneaththewaves.net/Software/XMPPPeek.html)
2. Create a self-signed certificate with the following command

   `openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

3. Edit xmpppeek.py and change port to 5223

4. Look at the  [the protocol documentation](protocol.md) for information on which
Ecovacs XMPP server is the right one for your Country. For example, a US user will
be using msg-na.ecouser.net. Find and note the IP address for the server.

5. Make sure the mobile App talks to your machine instead of the server. This can be
accomplished modifying your router's DNS configuration to have the Ecovacs domain
name point to your IP.

6. Run xmppeek as follows.

   `python ./xmpppeek.py <ECOVACS XMPP SERVER IP> cert.pem key.pem`

## Reset robot to factory settings

Ecovacs robots have an undocumented hardware reset button that can be useful
in case you run into trouble. Under the dustbin lid there is a small round hole
that hides the button (confirmed on models M80 and M81).

With the robot on, use something thin like a paper clip or needle to press and
hold the reset button. After about three seconds the robot will beep three times
to indicate successful reset.

You will have to delete the robot from the mobile app and go through the setup
process.

## Do release

- change version in `setup.py` (*commit message `bump version to A.B.C`*)
- create [new release](https://github.com/mib1185/py-sucks/releases/new)
  - create new tag for this commit as `vA.B.C`
  - set release-name to A.B.C
  - add noteworthy changes/PRs in description
- GitHub workflow [publish.yaml](https://github.com/mib1185/py-sucks/blob/master/.github/workflows/publish.yaml) will build the package and upload it to PyPi
