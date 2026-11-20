# Saptarshi Majumdar — personal website

Static personal homepage for **https://saptarshi7889.github.io/**.

- `index.html`: biography, background, profile links, and project links.
- `quenched.html`: constant-momentum papers, code/header links, and animation.
- `driven.html`: constant-force papers, code/header links, and animations.
- `style.css`: desktop and mobile layout.
- `media/quenched/`: relaxation and quantum-flutter MP4/GIFs, previews,
  rendering/loading scripts, sampled data, source manifests and logs.
- `.nojekyll`: serve the static files directly with GitHub Pages.

The Bose-polaron solver is a separate project website. This homepage links to
its existing address. The quenched page serves both recorded animations from
local `media/quenched/` assets; the driven page reuses the project website’s
public simulation media. The homepage has no animations. Code links target release v0.3.1.
This site does not modify the solver repository or website.

## Preview locally

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/`, then stop with Ctrl+C.

## Publish

The GitHub repository must be named **saptarshi7889.github.io**.
For the automatic versioned deployment, open **Settings → Pages** once and choose:

- **Source:** GitHub Actions

The `Publish website` workflow runs after every push or merge to `main`.
It builds and deploys the site without installing dependencies or creating commits.
Wait for that workflow to succeed. The personal site
will be at `https://saptarshi7889.github.io/`; project websites retain their
existing repository-specific addresses.

The build adds the deployed commit SHA to local page, CSS, JavaScript, image,
and video URLs, replacing manually maintained version parameters. Every page
checks `release.json` without browser caching when opened or refocused, and
redirects to a versioned URL if a newer deployment is available. This preserves
the page's fragment (for example, `#repulsive`). The check does not run in local
`file:` previews and does not clear unrelated browser data.

GitHub Pages still controls HTTP cache headers. The first deployment of this
mechanism may require one ordinary cache expiry or hard refresh because older
pages do not yet contain the version check. A merge is visible only after its
deployment finishes; this does not bypass deployment time or CDN propagation.

## Add another project

Add another project entry under the `projects` section in `index.html`, linking
to that repository's own GitHub Pages address. Keep its source and deployment
in its separate repository.

## Quenched animation sources

Both quenched animations and their supporting files live together in
`media/quenched/`. See [the animation README](media/quenched/README.md) for
parameters, original data locations and rendering commands. Cached sampled
arrays are included; the large original simulation archives remain external.
Run render/load commands from `media/quenched/` using the existing animation
environment. Bytecode caches are ignored by Git. Rerendering replaces media
files, so inspect the output before committing and pushing the website.
