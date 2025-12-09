from conways_physics.app import ConwaysPhysics


def test_status_initializing_message_on_compose():
    app = ConwaysPhysics()
    _ = list(app.compose())
    assert app.status.text == "initializing...please wait!"
