import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from ks.screens import SCREENS, check_screens

FIXTURES = Path(__file__).parent / 'fixtures'
PHONES = tuple(screen for screen in SCREENS if screen.phone)


def by_name(results):
    return {result.screen.name: result for result in results}


def closed_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def test_a_600px_element_scrolls_phones_sideways_and_no_desktop(tmp_path):
    results = by_name(check_screens(str(FIXTURES / 'too-wide.html'), SCREENS, tmp_path))

    for screen in SCREENS:
        result = results[screen.name]
        assert result.load_error is None, screen.name
        assert Path(result.file).stat().st_size > 1000, screen.name
        assert 'fixture console error' in ' '.join(result.console_errors), screen.name
        if screen.phone:
            assert result.wide_by > 150, screen.name
            assert 'div.hero' in ' '.join(result.wide_elements), screen.name
            assert 'table' not in ' '.join(result.wide_elements), screen.name
        else:
            assert result.wide_by == 0, screen.name


def test_a_page_that_fits_has_no_sideways_scroll_and_its_error_is_caught(tmp_path):
    results = check_screens(
        str(FIXTURES / 'fits.html'), PHONES, tmp_path, full_page=True
    )

    assert len(results) == 3
    for result in results:
        assert result.wide_by == 0, result.screen.name
        assert result.viewport_meta, result.screen.name
        assert 'fixture page error' in ' '.join(result.page_errors), result.screen.name


def test_a_server_that_is_down_is_a_load_error_not_a_crash(tmp_path):
    android = tuple(s for s in SCREENS if s.name == 'android')

    results = check_screens(f'http://127.0.0.1:{closed_port()}', android, tmp_path)

    assert 'ERR_CONNECTION_REFUSED' in results[0].load_error


def test_a_page_that_clips_its_overflow_cannot_scroll_sideways(tmp_path):
    results = check_screens(str(FIXTURES / 'clipped-page.html'), PHONES, tmp_path)

    for result in results:
        assert result.wide_by == 0, result.screen.name


def test_a_page_with_no_viewport_tag_is_caught_on_a_phone(tmp_path):
    iphone = tuple(s for s in SCREENS if s.name == 'iphone')

    results = check_screens(str(FIXTURES / 'no-viewport.html'), iphone, tmp_path)

    assert results[0].viewport_meta is False


def test_an_http_error_page_keeps_its_status(tmp_path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(FIXTURES))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    android = tuple(s for s in SCREENS if s.name == 'android')

    try:
        url = f'http://127.0.0.1:{server.server_port}/missing.html'
        results = check_screens(url, android, tmp_path)
    finally:
        server.shutdown()

    assert results[0].status == 404


def test_a_browser_that_fails_to_start_is_a_load_error_on_its_screens(
    tmp_path, monkeypatch
):
    from playwright.sync_api import BrowserType, Error

    def refuse(*_args, **_kwargs):
        raise Error('no browser here')

    monkeypatch.setattr(BrowserType, 'launch', refuse)
    firefox = tuple(s for s in SCREENS if s.engine == 'firefox')

    results = check_screens(str(FIXTURES / 'fits.html'), firefox, tmp_path)

    assert [r.load_error for r in results] == [
        'firefox did not start: no browser here'
    ] * 2
