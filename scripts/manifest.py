#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import urlopen
from packaging.version import Version

UPSTREAM_REPOSITORY = 'metatube-community/jellyfin-plugin-metatube'
REPOSITORY = os.environ.get('GITHUB_REPOSITORY', UPSTREAM_REPOSITORY)


def md5sum(filename) -> str:
    with open(filename, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_jellyfin_version(csproj: str) -> str:
    tree = ET.parse(csproj)
    root = tree.getroot()

    for pkg in root.iter("PackageReference"):
        if pkg.attrib.get("Include") in ("Jellyfin.Controller", "Jellyfin.Model"):
            return Version(pkg.attrib.get("Version")).base_version

    raise Exception("Jellyfin version not found")


def generate(filename, version, csproj) -> dict:
    return {
        'checksum': md5sum(filename),
        'changelog': 'Auto Released by Actions',
        'targetAbi': f'{get_jellyfin_version(csproj)}.0',
        'sourceUrl': f'https://github.com/{REPOSITORY}/releases/download/'
                     f'v{version}/Jellyfin.MetaTube@v{version}.zip',
        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'version': version
    }


def load_manifest() -> list:
    # A fork has no dist branch until its first release, so start from the upstream manifest.
    for repository in dict.fromkeys((REPOSITORY, UPSTREAM_REPOSITORY)):
        try:
            with urlopen(f'https://raw.githubusercontent.com/{repository}/dist/manifest.json') as f:
                return json.load(f)
        except HTTPError as e:
            if e.code != 404:
                raise

    raise Exception("Manifest not found")


def main() -> None:
    filename = sys.argv[1]
    version = filename.split('@', maxsplit=1)[1] \
        .removeprefix('v') \
        .removesuffix('.zip')

    csproj = os.path.join(os.path.dirname(__file__),
                          "../Jellyfin.Plugin.MetaTube/Jellyfin.Plugin.MetaTube.csproj")

    manifest = load_manifest()

    manifest[0]['versions'].insert(0, generate(filename, version, csproj))

    with open('manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)


if __name__ == '__main__':
    main()
