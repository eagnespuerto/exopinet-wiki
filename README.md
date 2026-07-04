# ExoPiNet Wiki

An offline exoplanet reference for Raspberry Pi OS. Downloads and caches data
from the [Open Exoplanet Catalogue](https://github.com/OpenExoplanetCatalogue/open_exoplanet_catalogue)
and the [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/),
then lets you browse it locally without a network connection.

Compatible with **32-bit Raspberry Pi OS** on **Pi Zero and above** (ARMv6+).

## Features

- One-shot data sync from OEC + NASA Exoplanet Archive
- Fully offline browsing after the first sync
- Search by planet or host-star name
- Sort by name, discovery year, radius, mass, orbital period, or
  Earth Similarity Index (ESI)
- Planet-type illustrations (terrestrial, super-Earth, mini-Neptune,
  Neptune-like, gas giant) generated from the shipped SVG templates
- Runs on the standard Python 3 + Tkinter stack already present on Pi OS

## Install

From a terminal on Raspberry Pi OS:

```bash
git clone https://github.com/YOUR_USER/exopinet-wiki.git
cd exopinet-wiki
sudo ./install.sh
```

This will:

1. `apt install` the runtime dependencies (`python3-tk`, `python3-requests`,
   `python3-pil`, `python3-pil.imagetk`)
2. Copy the app to `/opt/exopinet-wiki`
3. Symlink `/usr/local/bin/exopinet-wiki`
4. Install a menu entry under **Science** and **Education**

Launch from the menu or with:

```bash
exopinet-wiki
```

On first run, choose **File → Update Data** to fetch the catalogues (~a few
MB). All subsequent launches work offline.

## Uninstall

```bash
sudo ./uninstall.sh
```

The local data cache lives at `~/.local/share/exopinet-wiki/` and is left in
place; delete it manually if you also want to remove the cached catalogue.

## Rebuilding the planet artwork

The BMP files in `assets/bmp/` are generated from the SVG sources in
`assets/svg/` via:

```bash
python3 scripts/build_assets.py
```

Requires Pillow. End users never need to run this — the BMPs are shipped in
the repo.

## Data sources & credit

- Open Exoplanet Catalogue — CC0, Hanno Rein et al.
- NASA Exoplanet Archive — public domain, NASA/Caltech IPAC.

Please cite both if you publish anything using the data.

## License

MIT. See [LICENSE](LICENSE).
