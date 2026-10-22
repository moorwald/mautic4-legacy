# Source, licence and redistribution handoff

The community image recipe/modifications are GPL-3.0-or-later. Sven confirmed on 2026-10-22 that Docker-Mautic follows the same Mautic GPL licence. This is the recorded licensing basis for the preserved upstream Docker components despite the pinned snapshot lacking a separate LICENSE file; attribution and source remain intact. The exact upstream Mautic licence and its third-party notices are preserved in LICENSE and in the unchanged application distribution. Other bundled components retain their own licences; the image label does not relicense PHP, Debian packages or third-party libraries.

Each published r1 pair is accompanied by a public GitHub Release source bundle and checksum manifest, assembled from the actual tested images before pushing them. It contains:

- The exact package inventory of both images, mapping binary package/version to source package/version.
- All corresponding files listed for EVERY installed Debian/Sury source package, not just PHP. Their SHA-256 and sizes are checked against source indexes, whose signed InRelease metadata is independently verified with the images' public archive keyrings.
- Signed repository/index evidence, source URLs and hashes so the original package source/build recipes and distribution modifications can be inspected.
- The pinned prepared Mautic 4.4.13 archive including PHP dependency sources/notices, PLUS the complete upstream source/build-tree archive at its verified release commit.
- The exact upstream docker-mautic baseline source archive and the current community project's committed source/build/test recipes.
- Composer's pinned upstream source archive and licence/copyright texts from the installed PHAR.
- Installed-package copyright files, shared licence texts, the preserved upstream LICENSE and project NOTICE.

Source copies are retained as release assets instead of relying solely on external package URLs remaining available. Reproduce collection with:
```sh
python3 tools/source_handoff.py
```
This reads local build images, fetches public sources and creates ignored artifacts/source-handoff/. It does not install packages on the host, execute downloaded source builds, read production data or obtain credentials.

For a downloaded release, verify outer SHA256SUMS, extract source-bundle.tar, then verify source-bundle/SHA256SUMS. source-manifest.json maps files and package versions. The project source is in moorwald-source.tar; distribution-specific source packages include their own build/control/patch recipes. Required build tools and original vendor build requirements remain those documented in those sources.

The source bundle is not a claim that the whole image is bit-for-bit reproducible from a frozen Debian snapshot, nor a legal opinion. Base and PHP inputs are pinned; ordinary Debian package updates are recorded from the actual image. All complete licence/notice texts travel with their respective source/distribution files. Do not remove those notices or replace the source bundle with a short generic disclaimer.

No future Mautic support or application-library backport commitment is created. This handoff is for the exact released emergency image pair and its included components.
