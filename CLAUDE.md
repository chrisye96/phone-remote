# CLAUDE.md

Rules for working in this repository.

## Releases

Every release post must say, in both English and Chinese, which file to download for each system.

- Windows: `PhoneRemote.exe`
- Mac with an Apple chip: `PhoneRemote-macOS-AppleSilicon.zip`
- Mac with an Intel processor: `PhoneRemote-macOS-Intel.zip`

The post also tells Mac users how to get past the first-open block (the app is not signed with an Apple developer account) and to turn it on under Accessibility.

The two languages are not mixed: the whole guide in English first, then the whole guide in Chinese, with links at the very top that jump to each. The jump targets are explicit `<a name="en"></a>` and `<a name="zh"></a>` tags inside the headings, because headings on a release page get no anchors of their own.

The text lives in `.github/release-notes.md`. The release workflow (`.github/workflows/release.yml`) puts that file at the top of every post, above the generated list of changes, so the rule holds without anyone remembering it. When the set of downloadable files changes, update that file in the same change. After a release is published, read the post once to confirm the section is there.
