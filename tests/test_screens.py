import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from ks.screens import SCREENS, Result, problems_of, report_lines, target_url

KS = Path(sys.executable).parent / 'ks'
BY_NAME = {screen.name: screen for screen in SCREENS}


def clean(name):
    return Result(screen=BY_NAME[name], file=f'/out/{name}.png', status=200)


def ks_screens(*args):
    return subprocess.run(
        [KS, 'screens', *args], check=False, capture_output=True, text=True
    )


def test_phone_screens_cover_every_browser_engine():
    engines = {screen.engine for screen in SCREENS if screen.phone}

    assert engines == {'webkit', 'chromium', 'firefox'}


def test_an_unknown_screen_is_refused_with_every_valid_name():
    result = ks_screens('http://localhost:3000', '--screens', 'iphone,nokia')

    assert result.returncode == 2
    assert 'nokia' in result.stderr
    for screen in SCREENS:
        assert screen.name in result.stderr


def test_a_target_becomes_a_url():
    assert (
        target_url('https://a.example/p?q=1', Path('/w')) == 'https://a.example/p?q=1'
    )
    assert (
        target_url('localhost:3000/pricing', Path('/w'))
        == 'http://localhost:3000/pricing'
    )
    assert target_url('127.0.0.1:8080', Path('/w')) == 'http://127.0.0.1:8080'
    assert (
        target_url('localhost:3000/index.html', Path('/w'))
        == 'http://localhost:3000/index.html'
    )
    assert (
        target_url('example.com/about.htm', Path('/w'))
        == 'http://example.com/about.htm'
    )
    assert target_url('index.html', Path('/w')) == 'file:///w/index.html'
    assert target_url('site/index.html', Path('/w')) == 'file:///w/site/index.html'
    assert target_url('/abs/page.html', Path('/w')) == 'file:///abs/page.html'


def test_a_clean_screen_has_no_problems():
    assert problems_of(clean('iphone')) == []


def test_each_fault_is_a_problem():
    down = replace(clean('iphone'), file=None, status=None, load_error='refused')
    wide = replace(clean('iphone'), wide_by=210, wide_elements=['div.hero (600px)'])

    assert problems_of(down) == ['did not load: refused']
    assert '500' in ' '.join(problems_of(replace(clean('iphone'), status=500)))
    assert '210px' in problems_of(wide)[0] and 'div.hero' in problems_of(wide)[0]
    assert 'boom' in ' '.join(
        problems_of(replace(clean('iphone'), page_errors=['boom']))
    )
    assert 'nope' in ' '.join(
        problems_of(replace(clean('iphone'), console_errors=['nope']))
    )


def test_a_missing_viewport_tag_is_a_problem_on_phones_only():
    assert len(problems_of(replace(clean('iphone'), viewport_meta=False))) == 1
    assert problems_of(replace(clean('desktop-chrome'), viewport_meta=False)) == []


def test_the_report_names_each_screen_its_file_and_its_problems():
    lines = report_lines(
        [clean('iphone'), replace(clean('android'), page_errors=['boom'])], '/out'
    )
    text = '\n'.join(lines)

    assert '/out/iphone.png' in text
    assert 'boom' in text
    assert lines[-1].endswith('1 problem.')
    assert report_lines([clean('iphone')], '/out')[-1].endswith('no problems.')


def test_the_report_says_a_webkit_iphone_is_not_real_ios():
    assert 'not real iOS' in '\n'.join(report_lines([clean('iphone')], '/out'))
