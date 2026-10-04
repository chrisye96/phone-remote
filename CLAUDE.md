# CLAUDE.md

Rules for working in this repository.

## Releases

Every release post must say, in both English and Chinese, which file to download for each system.

- Windows: `PhoneRemote.exe`, attached to the release under Assets.
- macOS: there is no packaged app, so the post says so and points to the "run from source" steps in the README. If a Mac build is ever added, name its file in the post.

The text lives in `.github/release-notes.md`. The release workflow (`.github/workflows/release.yml`) puts that file at the top of every post, above the generated list of changes, so the rule holds without anyone remembering it. When the set of downloadable files changes, update that file in the same change. After a release is published, read the post once to confirm the section is there.
