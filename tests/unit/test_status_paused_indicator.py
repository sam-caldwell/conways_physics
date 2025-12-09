from conways_physics.app import ConwaysPhysics


def _compose_app() -> ConwaysPhysics:
    app = ConwaysPhysics()
    _ = list(app.compose())
    return app


def test_status_shows_paused_when_not_running():
    app = _compose_app()
    # App starts paused; updating status should include the indicator
    app._update_status()
    assert "[Paused]" in app.status.text


def test_status_hides_paused_when_running():
    app = _compose_app()
    app.action_resume()
    app._update_status()
    assert "[Paused]" not in app.status.text
