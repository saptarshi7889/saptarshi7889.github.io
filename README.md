# Saptarshi Majumdar — personal website

Static personal homepage for **https://saptarshi7889.github.io/**.

- `index.html`: biography, background, profile links, and project links.
- `quenched.html`: constant-momentum papers, code/header links, and animation.
- `driven.html`: constant-force papers, code/header links, and animations.
- `style.css`: desktop and mobile layout.
- `media/quenched/`: replacement MP4/GIF and preview for the quenched page.
- `.nojekyll`: serve the static files directly with GitHub Pages.

The Bose-polaron solver is a separate project website. This homepage links to
its existing address. The quenched page serves its replacement animation from
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
After pushing the `main` branch, open **Settings → Pages** and choose:

- **Source:** Deploy from a branch
- **Branch:** main
- **Folder:** / (root)

Save, then wait for GitHub's Pages deployment to complete. The personal site
will be at `https://saptarshi7889.github.io/`; project websites retain their
existing repository-specific addresses.

## Add another project

Add another project entry under the `projects` section in `index.html`, linking
to that repository's own GitHub Pages address. Keep its source and deployment
in its separate repository.
