# Доступность функций по странам и языкам: iOS 27.0.1 (24A446)

Исследовано 23 октября 2026. Статический анализ локального dyld cache iPhone15,4
через ipsw 3.1.738. Адреса ниже — виртуальные адреса без ASLR slide.
На устройстве overrides не применялись. Эти выводы не подтверждают работу на iOS 27.1.
Accessibility Settings в этом исследовании не использовались.

## Результат

Найден конкретный кандидат для отдельного экспериментального твика: разрешение
записи звонков через eligibility-домен **NICKEL (29)**. Подтверждена проверка в
клиентском коде, но доставка override и его принятие eligibilityd на этой сборке
не проверены. Готового проверенного регионального или языкового unlock нет.

Два привлекательных ключа Translation отсеяны: один уже включён по умолчанию,
другой ограничен InternalBuild и выбирает те же списки языков в этой сборке.
Простой override очереди Apple Intelligence также нельзя считать рабочим:
найден профильный путь с криптографической проверкой подписи.

## 1. Запись звонков: NICKEL, домен 29

Подтверждённая цепочка:

1. `+[TUEligibilityChecker isCallRecordingEligible]` по `0x19e8375d8`
   передаёт `w2 = 0x1d` (29).
2. ObjC selector stub `0x1a00a79f0` выбирает `isDomainEligible:`.
3. `+[TUEligibilityChecker isDomainEligible:]` по `0x19e899670`
   вызывает `os_eligibility_get_domain_answer` и возвращает true только при
   успешном вызове и `answer == 4`; при ошибке возвращает false.
4. `os_eligibility_domain_for_name` в libsystem_eligibility возвращает 29 для
   `OS_ELIGIBILITY_DOMAIN_NICKEL` (ветка возврата `0x2c2cce71c`).
5. `_TUCallRecordingActivatable` действительно включает eligibility в итоговую
   проверку. Также присутствуют отдельные проверки устройства, feature flags,
   TTS, server bag и MDM. Ответ 4 устраняет только один барьер.

Это **не обычный preference `NICKEL=true`**. Возможное направление — отдельный
eligibility override для ID 29. В репозитории уже есть архив для Siri AI
(`src/tweaks/siri_ai.py`), но его overrideMap содержит только 96, 122 и 155:
AMERICIUM, GREYMATTER, SIRI_MODE. NICKEL он не включает. Формат — NSKeyedArchive,
а не словарь plist для Managed Preferences. Наличие клиентского API
`os_eligibility_force_domain_answer` само по себе не доказывает доступ без
привилегий или entitlement.

Перед добавлением в приложение требуется подтвердить схему архива в eligibilityd,
принятие записи для 29, сохранение результата после перезагрузки и появление
функции на устройстве с исходным отрицательным региональным ответом. Нельзя просто
расширить существующий Siri AI switch: он сейчас ограничен точной версией 27.0,
а его payload заменяет весь архив overrides.

Доказательства: `evidence/call-recording-*.txt`, `domain-for-name-full.txt`,
`domain-ids.json`; текущий состав Siri payload проверяет `tools/test_siri_ai.py`.

## 2. Скрытые языки перевода звонков: ключ существует, unlock не подтверждён

Точное значение ключа: `IncludeHiddenCallTranslationLocales`.
Экспорт `kLTDebugIncludeHiddenCallTranslationLocales` по `0x26930f158`
указывает на CFString `0x275c5d6e0` → cstring `0x24c660e55`.

`_LTPreferencesIncludeHiddenCallTranslationLocales` (`0x2421e1bc8`) вызывает
`_LTPreferencesBooleanForKey(key, false)`. Helper использует
`NSUserDefaults.standardUserDefaults`, `objectForKey:`, проверяет NSNumber и
читает bool; конкретный persistent preferences domain только этим не доказан.

Но потребитель `+[_LTDASRAssetService supportedLanguagesForTaskHint:]`
(`0x2421b1e60`) для task 9/10 **сначала** вызывает `_LTIsInternalInstall`.
При false чтение ключа пропускается. `_LTIsInternalInstall` (`0x24c63d160`)
читает `MGCopyAnswer("InternalBuild")`.

Более того, декодирование NSConstantArray показало: обычный и скрытый списки
**одинаковы** для обеих веток в 24A446:

`de_DE, en_GB, en_US, es_ES, fr_FR, pt_BR, zh_CN, ja_JP, ko_KR, it_IT, zh_TW`.

Массивы task9: `0x2753d5d18` / `0x2753d5d30`; task10:
`0x2753d5d48` / `0x2753d5d60`. У каждого count=11.
Русского языка в этих массивах нет. Этот ключ не стоит добавлять как рабочий
тумблер «дополнительные языки звонков». Глобальную подмену InternalBuild не
исследовали и не предлагаем как способ включить одну функцию.

Отдельная находка: `-[_LTTranslationServer task:isSupportedInCountry:completion:]`
(`0x24222d0f8`) в этой сборке асинхронно возвращает true — в блоке `0x24222d190`
в completion передаётся `w1=1`. Значит, этот конкретный endpoint не является
местом реальной региональной блокировки; другие уровни доступа не исключены.

Доказательства: `translation-hidden-*`, `translation-internal-install.txt`,
`translation-country-check.txt`, `translation-locale-arrays.json`,
`resolved-constants.json`.

## 3. AI-языки в задачах перевода: по умолчанию уже разрешены

Точный ключ: `IncludeAIOnlyLanguagesInAllTasks`.
Его функция имеет другое имя: `_LTPreferencesIncludeAILanguagesInAllTasks`
(`0x2421df990`). Она вызывает boolean helper с **default=true**.

Потребитель `-[_LTDLanguageAssetCache _filterAILanguages:forTaskHint:]`
(`0x2421d283c`) действительно использует результат. В одной из веток true
возвращает исходный список без дополнительной фильтрации AI-языков; при false
включается фильтрация. В начале есть отдельный путь через статус LLM translation,
поэтому значение true не отменяет все проверки этой функции.

Принудительное true может изменить поведение, если где-то явно сохранено false,
но на чистом defaults это не новая разблокировка и не способ установить
отсутствующие языковые модели.

Доказательства: `translation-ai-*`, `translation-bool-helper.txt`,
`translation-defaults-stub.txt`, `resolved-constants.json`.

## 4. Apple Intelligence: несколько независимых ограничений

В GenerativeModels присутствуют разные причины недоступности:
`selectedLanguageIneligible`, `selectedSiriLanguageIneligible`,
`selectedLanguageDoesNotMatchSelectedSiriLanguage`, `regionIneligible`,
`countryLocationIneligible`, `localeIneligible`,
`useCaseDoesNotSupportRequestedLanguage`,
`useCaseDoesNotAllowCurrentIPCountryCode`,
`useCaseDoesNotAllowUserLocaleRegion`.

Это строки причин/диагностики, а не имена preference keys. Нельзя превратить их
в switches записью true/false и обещать поддержку языка.

Подтверждён отдельный активный региональный путь:
`GMAvailabilityWrapper.isSensitiveRegionForEnhancedSiri` (`0x1872958a0`)
читает MobileGestalt regionCode и сравнивает с `CH`. Это аппаратный региональный
ответ MobileGestalt; наличие этого пути не доказывает, что одной смены региона
в Settings хватит для доступности Siri.

Ключи `com.apple.gms.availability.forcedWaitlistStatus` и
`...forcedWaitlistStatus.attestation` выглядят перспективно, но
`AvailabilityStore.forcedWaitlistStatusFromProfileOverride` (`0x18727f854`)
вызывает `SecKeyVerifySignature` с
`kSecKeyAlgorithmRSASignatureMessagePKCS1v15SHA256`, отвергает отсутствие/неверную
подпись и принимает только подписанное значение accepted. В строках также есть
запрет secure setter на non-internal builds. Это конкретный профильный путь;
вывод не означает, что абсолютно все альтернативные overrides имеют ту же
защиту. `...forcedAvailability` найден как строка, его полный путь не исследован,
рабочим кандидатом пока не считается.

Доказательства: `gm-forced-profile.txt`, `gm-sensitive-region.txt`,
`GenerativeModels-selected.txt`.

## 5. Карта направлений для следующего исследования

Восстановлена таблица из 220 имён (включая INVALID). Выбранные домены:

| Домен | ID | Что подтверждено |
|---|---:|---|
| NICKEL | 29 | Потребитель — разрешение записи звонков, принимает answer 4 |
| FOUNDATION_MODELS | 130 | Имя и ID; потребитель и работа override ещё не проверены |
| PERSONAL_QA | 127 | Имя и ID; назначение нельзя доказать одним названием |
| SIRI_WITH_APP_INTENTS | 128 | Имя и ID; потребитель и override ещё не проверены |
| PODCASTS_TRANSCRIPTS | 121 | Имя и ID; региональный обход ещё не проверен |
| FORCED_SHUTTER_SOUND | 126 | Имя и ID; управление звуком камеры не доказано потребителем |

OSEligibility различает страну нахождения, страну аккаунта/биллинга, язык устройства,
язык Siri, locale и совпадение языков. RegulatoryDomain экспортирует обновления
оценки страны из MCC, Wi-Fi AP, GeoIP и peer, а также содержит приоритеты этих
источников. Поэтому регион интерфейса нельзя считать универсальной подменой
всех страновых сигналов. Это вывод об архитектуре доступных интерфейсов, а не
подтверждённый полный алгоритм eligibilityd.

## Ограничения и официальная сверка

Apple отдельно требует совпадения поддерживаемых языков устройства и Siri,
скачанных моделей и совместимого устройства; отдельно описывает ограничения
материкового Китая. Русского нет в опубликованном списке Apple Intelligence для
iOS 27: [официальная справка Apple](https://support.apple.com/en-ie/121115),
проверено 23 октября 2026, страница от 15 сентября 2026.
Положительный локальный eligibility answer не доказывает наличие языковой модели
или принятие запроса сервером.

Код приложения в рамках этого исследования не менялся. Результаты — доказанная
клиентская проверка записи звонков, карта следующих направлений и отсев ложных
plist-твиков; готовый работающий обход на устройстве не заявляется.

## Воспроизводимость

Cache UUID: `A757941A-CCAB-3181-9C03-10AE25FEA7B2`.
Исходник: `artifacts/24A446__iPhone15,4/dyld_shared_cache_arm64e` в соседнем
проекте reversing, вместе с subcaches. `firmware-identity.json` сохранён рядом.

Примеры команд (DSC — путь к cache):

```sh
ipsw dyld disass "$DSC" --vaddr 0x19e8375d8 --count 28
ipsw dyld disass "$DSC" --vaddr 0x19e899670 --count 65
ipsw dyld disass "$DSC" --vaddr 0x2c2ccd180 --count 1600
ipsw dyld xref "$DSC" 0x2421e1bc8 --image TranslationDaemon
ipsw dyld disass "$DSC" --vaddr 0x2421b1e60 --count 210
ipsw dyld disass "$DSC" --vaddr 0x24c63d160 --count 90
ipsw dyld disass "$DSC" --vaddr 0x18727f854 --count 420
```

CFString/NSConstantArray декодированы из mapped cache bytes; для конкретных
chained pointers этой сборки VA = cache base 0x180000000 + low32(pointer).
Это описание использованного формата, не универсальный декодер любых cache.
Имена task9/task10 оставлены числовыми: их полная enum-семантика не восстановлена.
Хеши сохранённых артефактов перечислены в `SHA256SUMS`.
