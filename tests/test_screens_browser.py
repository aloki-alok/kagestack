import socket
from pathlib import Path

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
