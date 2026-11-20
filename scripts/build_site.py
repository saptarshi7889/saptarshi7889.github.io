"""Prepare a versioned GitHub Pages artifact using only the standard library."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
ATTRIBUTES = re.compile(r'\b(href|src|poster)="([^"]+)"')
EXCLUDED_DIRECTORIES = {".github", "scripts", "tests"}
REFRESH_SCRIPT = """<script>
(() => {
  const revision = document.querySelector('meta[name="site-revision"]').content;
  async function checkVersion() {
    if (location.protocol === 'file:') return;
    try {
      const release = new URL('release.json', location.href);
      release.searchParams.set('check', Date.now().toString());
      const response = await fetch(release, {cache: 'no-store'});
      if (!response.ok) return;
      const {revision: latest} = await response.json();
      if (!/^[a-f0-9]{40}$/.test(latest) || latest === revision) return;
      const target = new URL(location.href);
      if (target.searchParams.get('v') === latest) return;
      target.searchParams.set('v', latest);
      location.replace(target.href);
    } catch {
      // Keep the current page usable when offline or a deployment is unavailable.
    }
  }
  window.addEventListener('pageshow', checkVersion);
  window.addEventListener('focus', checkVersion);
})();
</script>"""


def version_url(match, page, revision):
    attribute, value = match.groups()
    url = urlsplit(value)
    if url.scheme or url.netloc or not url.path:
        return match.group()
    target = ROOT / unquote(url.path.lstrip('/')) if url.path.startswith('/') else page.parent / unquote(url.path)
    if not target.is_file():
        return match.group()
    query = dict(parse_qsl(url.query, keep_blank_values=True))
    query['v'] = revision
    versioned = urlunsplit(url._replace(query=urlencode(query)))
    return f'{attribute}="{versioned}"'


def build(destination, revision):
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('Expected a full Git commit SHA for the site revision')
    if destination.exists():
        raise ValueError('Build destination must not already exist')
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    destination.mkdir(parents=True)
    for name in filter(None, files):
        relative = Path(name)
        if relative.parts[0] in EXCLUDED_DIRECTORIES or name == '.gitignore':
            continue
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == '.html':
            content = ATTRIBUTES.sub(lambda match: version_url(match, source, revision), source.read_text())
            content = content.replace('</head>', f'<meta name="site-revision" content="{revision}">\n{REFRESH_SCRIPT}\n</head>')
            target.write_text(content)
        else:
            shutil.copyfile(source, target)
    (destination / 'release.json').write_text(json.dumps({'revision': revision}) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    arguments = parser.parse_args()
    build(arguments.destination, arguments.revision)
