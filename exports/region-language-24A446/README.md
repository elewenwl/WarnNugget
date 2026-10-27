# Region & Language — Experimental 24A446

A .batter v3 package for GoldenNugget with Community Tweaks. Research was
limited to static analysis of iOS 27.0.1, build 24A446. Not tested on a device.
The packages are restricted to iOS 27.0.1; the format cannot restrict the exact build.

## Usage

1. Import RegionLanguage-Experimental-24A446.batter into Templates.
2. Open the template switches and select the operation you want.
3. NICKEL requires protective backup to be enabled, with backup encryption disabled.
4. Apply changes as usual. All operations are disabled by default.

## Contents

- NICKEL: an archive containing overrideMap {29: EligibilityOverrideData(answer=4)}.
  The call-recording consumer was confirmed, but acceptance of the new payload
  by eligibilityd was not. Other feature checks (device, server bag, MDM, etc.)
  remain. This is a candidate for testing, not a guarantee of activation.
- IncludeHiddenCallTranslationLocales=true: a research preference.
  The identified code path requires MobileGestalt InternalBuild. The normal and
  hidden locale lists are identical. This does not add Russian language support.
- IncludeAIOnlyLanguagesInAllTasks=true: a research preference.
  Already true by default; it may only help if an existing override sets it to false.

Translation uses ManagedPreferences/mobile/com.apple.translationd.
The preferences domain was inferred from the daemon; runtime reads from this
specific domain have not been confirmed. These entries are research controls,
not verified feature unlocks.

NICKEL uses GoldenNugget's supported path mapping:
/var/containers/Data/SystemGroup/com.apple.eligibilityd/Library/Caches/NeverRestore/eligibility_overrides.data
→ SysContainerDomain-com.apple.eligibilityd / Library/Caches/NeverRestore/eligibility_overrides.data,
owner/group 0. This is a logical path used by GoldenNugget, not a confirmed
physical system-container UUID path on a device. The archive was generated with
NSKeyedArchive UIDs and classes from the existing Project Linwood payload.
Offline decoding was checked; Foundation/eligibilityd unarchiving and device
application were not tested.

## Reset and interactions

NICKEL REPLACES the entire overrides file: existing Siri AI and other overrides
are not preserved. The new payload contains only domain 29; it does not activate
other domains. Turning the switch off prevents future writes but does not undo
an already applied change.
To clear overrides, import RegionLanguage-Reset-24A446.batter and select the
appropriate operation. Clear eligibility removes ALL overrides; it does not
restore the previous contents. Translation reset writes the identified defaults
(false/true); it does not remove the preference keys.
Do not apply an enable operation and its corresponding reset together; collection
rejects conflicting raw payloads targeting the same file.

FOUNDATION_MODELS, PERSONAL_QA, SIRI_WITH_APP_INTENTS, PODCASTS_TRANSCRIPTS and
FORCED_SHUTTER_SOUND remain in the research report: only their names and IDs have
been established. The signed forcedWaitlistStatus override is also excluded:
no working payload was obtained.

See research/REPORT.ru.md and the evidence files in this archive.
The research report is in Russian.

Eligibility archive structure source: mattisklein/project-linwood,
commit b9438cec65b384974a9c6be6169ec9fa1e64c83a, MIT.
https://github.com/mattisklein/project-linwood
The license and original source README are included in attribution/.
