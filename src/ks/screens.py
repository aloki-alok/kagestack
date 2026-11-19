import argparse
import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PLAYWRIGHT = 'playwright==1.65.0'
LOAD_MS = 30_000
SETTLE_MS = 5_000
DESKTOP = {'width': 1440, 'height': 900}


@dataclass(frozen=True)
class Screen:
    name: str
    engine: str
    phone: bool
    stands_for: str
    preset: str | None = None
    size: dict | None = None


SCREENS = (
    Screen(
        'iphone',
        'webkit',
        True,
        'Safari on iPhone: WebKit at iPhone size, close for layout, not real iOS',
        preset='iPhone 15',
    ),
    Screen('android', 'chromium', True, 'Chrome on Android', preset='Pixel 7'),
    Screen(
        'firefox-phone',
        'firefox',
        True,
        'Firefox at phone width, with no touch and a desktop user agent',
        size={'width': 390, 'height': 844},
    ),
    Screen('ipad', 'webkit', False, 'Safari on iPad', preset='iPad Mini'),
    Screen(
        'desktop-chrome', 'chromium', False, 'Chrome and Edge on a laptop', size=DESKTOP
    ),
    Screen('desktop-safari', 'webkit', False, 'Safari on a Mac', size=DESKTOP),
    Screen('desktop-firefox', 'firefox', False, 'Firefox on a laptop', size=DESKTOP),
)


@dataclass
class Result:
    screen: Screen
    file: str | None = None
    status: int | None = None
    load_error: str | None = None
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    wide_by: int = 0
    wide_elements: list[str] = field(default_factory=list)
    viewport_meta: bool = True


READ_LAYOUT = """() => {
  const root = document.documentElement, width = root.clientWidth
  const rootOverflow = getComputedStyle(root).overflowX
  const pageOverflow = rootOverflow === 'visible' && document.body
    ? getComputedStyle(document.body).overflowX : rootOverflow
  const canScroll = pageOverflow !== 'hidden' && pageOverflow !== 'clip'
  const overflowBy = Math.max(root.scrollWidth, document.body?.scrollWidth ?? 0) - width
  const wideBy = canScroll ? overflowBy : 0
  const viewportMeta = !!document.querySelector('meta[name="viewport"]')
  if (wideBy <= 0) return { wideBy: 0, wideElements: [], viewportMeta }
  const insideScrollBox = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement)
      if (getComputedStyle(p).overflowX !== 'visible') return true
    return false
  }
  const wide = [...document.body.querySelectorAll('*')]
    .filter(el => el.getBoundingClientRect().right > width + 1 && !insideScrollBox(el))
  const set = new Set(wide)
  const outermost = wide.filter(el => {
    for (let p = el.parentElement; p; p = p.parentElement) if (set.has(p)) return false
    return true
  })
  const label = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')
    + [...el.classList].slice(0, 2).map(c => '.' + c).join('')
  const right = el => Math.round(el.getBoundingClientRect().right)
  return {
    wideBy,
    wideElements: outermost.slice(0, 5).map(el => `${label(el)} (right edge ${right(el)}px)`),
    viewportMeta,
  }
}"""

URL_SCHEME = re.compile(r'^[a-z][a-z0-9+.-]*://', re.IGNORECASE)
HOST = re.compile(
    r'^(localhost|\d{1,3}(\.\d{1,3}){3}|[\w-]+(\.[\w-]+)+)(:\d+)?$', re.IGNORECASE
)
HTML_FILE = re.compile(r'\.html?$', re.IGNORECASE)


def target_url(target, cwd):
    if URL_SCHEME.match(target):
        return target
    host = target.split('/')[0]
    if HOST.match(host) and not HTML_FILE.search(host):
        return f'http://{target}'
    return (cwd / target).resolve().as_uri()


def problems_of(result):
    if result.load_error:
        return [f'did not load: {result.load_error}']
    problems = []
    if result.status and result.status >= 400:
        problems.append(f'the page answered HTTP {result.status}')
    if result.screen.phone and not result.viewport_meta:
        problems.append(
            'no <meta name="viewport"> tag, so phones show the desktop layout zoomed out'
        )
    if result.wide_by > 0:
        source = (
            f', from {", ".join(result.wide_elements)}' if result.wide_elements else ''
        )
        problems.append(
            f'scrolls sideways: {result.wide_by}px wider than the screen{source}'
        )
    problems += [f'uncaught error: {error}' for error in result.page_errors]
    problems += [f'console error: {error}' for error in result.console_errors]
    return problems


def report_lines(results, out):
    lines, count = [], 0
    for result in results:
        problems = problems_of(result)
        count += len(problems)
        mark = '✗' if problems else '✓'
        file = f'  {result.file}' if result.file else ''
        lines.append(f'{mark} {result.screen.name}: {result.screen.stands_for}{file}')
        lines += [f'    {problem}' for problem in problems]
    total = f'{count} problem{"" if count == 1 else "s"}.' if count else 'no problems.'
    return [*lines, '', f'screenshots in {out}. {total}']


def screen_list(text):
    names = [name.strip() for name in text.split(',') if name.strip()]
    by_name = {screen.name: screen for screen in SCREENS}
    unknown = [name for name in names if name not in by_name]
    if unknown:
        valid = ', '.join(by_name)
        raise argparse.ArgumentTypeError(
            f'no screen named {", ".join(unknown)}. the screens are: {valid}'
        )
    return tuple(by_name[name] for name in names)


def add_arguments(parser):
    parser.add_argument(
        'page', help='a URL, a host such as localhost:3000, or an HTML file'
    )
    parser.add_argument(
        '--screens',
        type=screen_list,
        default=SCREENS,
        metavar='NAMES',
        help=f'comma-separated, from: {", ".join(s.name for s in SCREENS)}',
    )
    parser.add_argument('--full', action='store_true', help='capture the whole page')
    parser.add_argument('--out', type=Path, help='folder for the screenshots')


def install_missing(playwright, engines):
    missing = [
        e for e in engines if not Path(getattr(playwright, e).executable_path).exists()
    ]
    if not missing:
        return
    print(f'ks: downloading {", ".join(missing)} for Playwright, once', file=sys.stderr)
    install = [sys.executable, '-m', 'playwright', 'install', *missing]
    if subprocess.run(install, stdout=sys.stderr, check=False).returncode:
        raise SystemExit(
            f'ks: could not download {", ".join(missing)}. on linux add --with-deps.'
        )


def check_one(context, screen, url, file, full_page):
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeout

    result = Result(screen)
    page = context.new_page()
    page.on(
        'console', lambda m: m.type == 'error' and result.console_errors.append(m.text)
    )
    page.on('pageerror', lambda error: result.page_errors.append(str(error)))
    try:
        response = page.goto(url, wait_until='load', timeout=LOAD_MS)
        result.status = response.status if response else None
        with contextlib.suppress(PlaywrightTimeout):
            page.wait_for_load_state('networkidle', timeout=SETTLE_MS)
        layout = page.evaluate(READ_LAYOUT)
        result.wide_by = layout['wideBy']
        result.wide_elements = layout['wideElements']
        result.viewport_meta = layout['viewportMeta']
        page.screenshot(path=str(file), full_page=full_page)
        result.file = str(file)
    except PlaywrightError as error:
        result.load_error = str(error).splitlines()[0]
    return result


def check_screens(page, screens, out, full_page=False, cwd=None):
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    url = target_url(page, cwd or Path.cwd())
    out.mkdir(parents=True, exist_ok=True)
    engines = list(dict.fromkeys(screen.engine for screen in screens))
    results = {}
    with sync_playwright() as playwright:
        install_missing(playwright, engines)
        for engine in engines:
            engine_screens = [s for s in screens if s.engine == engine]
            try:
                browser = getattr(playwright, engine).launch()
            except PlaywrightError as error:
                reason = f'{engine} did not start: {str(error).splitlines()[0]}'
                results |= {
                    s.name: Result(s, load_error=reason) for s in engine_screens
                }
                continue
            for screen in engine_screens:
                options = (
                    playwright.devices[screen.preset]
                    if screen.preset
                    else {'viewport': screen.size}
                )
                context = browser.new_context(**options)
                results[screen.name] = check_one(
                    context, screen, url, out / f'{screen.name}.png', full_page
                )
                context.close()
            browser.close()
    return [results[screen.name] for screen in screens]


def run(args):
    out = args.out or Path(
        tempfile.gettempdir()
    ) / 'ks-screens' / datetime.now().strftime('%Y%m%d-%H%M%S')
    results = check_screens(args.page, args.screens, out.resolve(), args.full)
    print('\n'.join(report_lines(results, out.resolve())))
    return 1 if any(problems_of(result) for result in results) else 0


def screens(args):
    try:
        import playwright  # noqa: F401
    except ImportError:
        uv = shutil.which('uv')
        if not uv:
            print(f'ks: screens needs uv, or {PLAYWRIGHT} installed', file=sys.stderr)
            return 2
        command = [
            uv,
            'run',
            '--quiet',
            '--no-project',
            '--python',
            sys.executable,
            '--with',
            PLAYWRIGHT,
            'python',
            __file__,
        ]
        os.execv(uv, [*command, *sys.argv[2:]])
    return run(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='ks screens')
    add_arguments(parser)
    sys.exit(run(parser.parse_args()))
