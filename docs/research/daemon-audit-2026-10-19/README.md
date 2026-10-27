# Проверка демонов GoldenNugget на симуляторе

Дата: 19 октября 2026. iPhone 17 Pro, CoreSimulator iOS 26.5 (23F77), x86_64.

В 46 зарегистрированных случаях подтверждённых циклов перезагрузки не обнаружено. Из 37 отдельных служб у 36 штатно завершается ожидание готовности загрузки; отключение `nanoregistryd` дважды вызывает таймаут при стабильной оболочке. Все четыре составные группы прошли проверку. При совместном отключении всех 37 служб также получен таймаут при стабильной оболочке. Три контрольных запуска без отключений прошли штатно. В реестре GoldenNugget 58 групп и 111 уникальных ключей; в этом runtime найдены 37 соответствующих launchd-служб. 74 ключа не представлены отдельными службами и не получили проверку отключения.

## Метод

Создан отдельный симулятор `GoldenNugget-Daemon-Audit` (`362457BA-2C1E-49CE-B6FB-DC7B1FEBD053`). Для каждого случая: `simctl spawn … launchctl disable DOMAIN/LABEL`, полное выключение и включение симулятора, ожидание `bootstatus -b` до 150 секунд, проверка сохранённого disabled-состояния и отсутствия целевой службы в launchd. Затем четыре замера PID/state/runs SpringBoard и backboardd с интервалами не менее пяти секунд и снимок экрана. Перед следующим случаем службы включаются обратно; следующий запуск применяет это состояние.

Для служб симулятора используются фактические домены `system` и `user/501`. Это проверка поведения CoreSimulator, а не применение `/var/db/com.apple.xpc.launchd/disabled.plist` через полный restore на iPhone. Физическое устройство, ядро iOS, аппаратные watchdog, iOS 27, длительное использование и функциональность отключённых служб не проверялись.

## Отдельные службы

| Ключ | Результат | Длительность случая, с |
|---|---|---:|
| `com.apple.UsageTrackingAgent` | [Штатная готовность, стабильная оболочка](key-com.apple.UsageTrackingAgent/result.json) | 53.9 |
| `com.apple.aslmanager` | [Штатная готовность, стабильная оболочка](key-com.apple.aslmanager/result.json) | 51.1 |
| `com.apple.assistant_service` | [Штатная готовность, стабильная оболочка](key-com.apple.assistant_service/result.json) | 54.1 |
| `com.apple.assistantd` | [Штатная готовность, стабильная оболочка](key-com.apple.assistantd/result.json) | 54.1 |
| `com.apple.assistivetouchd` | [Штатная готовность, стабильная оболочка](key-com.apple.assistivetouchd/result.json) | 56.7 |
| `com.apple.corespotlightservice` | [Штатная готовность, стабильная оболочка](key-com.apple.corespotlightservice/result.json) | 50.7 |
| `com.apple.coresymbolicationd` | [Штатная готовность, стабильная оболочка](key-com.apple.coresymbolicationd/result.json) | 51.7 |
| `com.apple.devicecheckd` | [Штатная готовность, стабильная оболочка](key-com.apple.devicecheckd/result.json) | 53.1 |
| `com.apple.diagnosticd` | [Штатная готовность, стабильная оболочка](key-com.apple.diagnosticd/result.json) | 49.7 |
| `com.apple.diagnosticextensionsd` | [Штатная готовность, стабильная оболочка](key-com.apple.diagnosticextensionsd/result.json) | 50.7 |
| `com.apple.familycircled` | [Штатная готовность, стабильная оболочка](key-com.apple.familycircled/result.json) | 51.2 |
| `com.apple.feedbackd` | [Штатная готовность, стабильная оболочка](key-com.apple.feedbackd/result.json) | 53.1 |
| `com.apple.followupd` | [Штатная готовность, стабильная оболочка](key-com.apple.followupd/result.json) | 55.4 |
| `com.apple.gamed` | [Штатная готовность, стабильная оболочка](key-com.apple.gamed/result.json) | 55.0 |
| `com.apple.geod` | [Штатная готовность, стабильная оболочка](key-com.apple.geod/result.json) | 54.5 |
| `com.apple.healthd` | [Штатная готовность, стабильная оболочка](key-com.apple.healthd/result.json) | 56.4 |
| `com.apple.itunescloudd` | [Штатная готовность, стабильная оболочка](key-com.apple.itunescloudd/result.json) | 56.7 |
| `com.apple.locationd` | [Штатная готовность, стабильная оболочка](key-com.apple.locationd/result.json) | 66.3 |
| `com.apple.logd` | [Штатная готовность, стабильная оболочка](key-com.apple.logd/result.json) | 56.1 |
| `com.apple.logd_helper` | [Штатная готовность, стабильная оболочка](key-com.apple.logd_helper/result.json) | 56.9 |
| `com.apple.logd_reporter` | [Штатная готовность, стабильная оболочка](key-com.apple.logd_reporter/result.json) | 59.4 |
| `com.apple.mediaremoted` | [Штатная готовность, стабильная оболочка](key-com.apple.mediaremoted/result.json) | 57.6 |
| `com.apple.nanoregistryd` | [Таймаут готовности; оболочка стабильна](key-com.apple.nanoregistryd/result.json) | 186.3 |
| `com.apple.nanotimekitcompaniond` | [Штатная готовность, стабильная оболочка](key-com.apple.nanotimekitcompaniond/result.json) | 50.9 |
| `com.apple.newsd` | [Штатная готовность, стабильная оболочка](key-com.apple.newsd/result.json) | 53.6 |
| `com.apple.parsecd` | [Штатная готовность, стабильная оболочка](key-com.apple.parsecd/result.json) | 52.2 |
| `com.apple.passd` | [Штатная готовность, стабильная оболочка](key-com.apple.passd/result.json) | 54.9 |
| `com.apple.rtcreportingd` | [Штатная готовность, стабильная оболочка](key-com.apple.rtcreportingd/result.json) | 54.2 |
| `com.apple.searchd` | [Штатная готовность, стабильная оболочка](key-com.apple.searchd/result.json) | 52.2 |
| `com.apple.shazamd` | [Штатная готовность, стабильная оболочка](key-com.apple.shazamd/result.json) | 52.1 |
| `com.apple.spotlightknowledged` | [Штатная готовность, стабильная оболочка](key-com.apple.spotlightknowledged/result.json) | 53.9 |
| `com.apple.spotlightknowledged.updater` | [Штатная готовность, стабильная оболочка](key-com.apple.spotlightknowledged.updater/result.json) | 49.4 |
| `com.apple.syslogd` | [Штатная готовность, стабильная оболочка](key-com.apple.syslogd/result.json) | 52.9 |
| `com.apple.tipsd` | [Штатная готовность, стабильная оболочка](key-com.apple.tipsd/result.json) | 52.6 |
| `com.apple.triald` | [Штатная готовность, стабильная оболочка](key-com.apple.triald/result.json) | 52.4 |
| `com.apple.videosubscriptionsd` | [Штатная готовность, стабильная оболочка](key-com.apple.videosubscriptionsd/result.json) | 52.9 |
| `com.apple.voiced` | [Штатная готовность, стабильная оболочка](key-com.apple.voiced/result.json) | 51.9 |

## nanoregistryd: воспроизводимый таймаут, не подтверждённый бутлуп

При отключении `com.apple.nanoregistryd` два запуска завершились таймаутом `bootstatus` на «Waiting on BackBoard». В обоих случаях SpringBoard и backboardd имели `state = running`, `runs = 1` и неизменный PID во всех четырёх замерах; домашний экран отображался. После включения службы контрольная загрузка прошла штатно. Это свидетельство воспроизводимого нарушения ожидания готовности в этом runtime, а не доказательство перезагрузок или бутлупа на iPhone.

[Первый запуск](key-com.apple.nanoregistryd/result.json), [повтор](repeat-com.apple.nanoregistryd/result.json), [контроль после включения](control-after-investigation/result.json).

## Составные проверки и контроль

| Случай | Ключей отключено | Результат |
|---|---:|---|
| baseline | 0 | [Штатная готовность, стабильная оболочка](baseline/result.json) |
| control-after-investigation | 0 | [Штатная готовность, стабильная оболочка](control-after-investigation/result.json) |
| group-CrashReports | 6 | [Штатная готовность, стабильная оболочка](group-CrashReports/result.json) |
| group-Diagnostics | 2 | [Штатная готовность, стабильная оболочка](group-Diagnostics/result.json) |
| group-Spotlight | 4 | [Штатная готовность, стабильная оболочка](group-Spotlight/result.json) |
| group-VoiceControl | 3 | [Штатная готовность, стабильная оболочка](group-VoiceControl/result.json) |
| combined-present | 37 | [Таймаут готовности; оболочка стабильна](combined-present/result.json) |
| control-final | 0 | [Штатная готовность, стабильная оболочка](control-final/result.json) |

В совместном случае подтверждено disabled-состояние всех 37 ключей и отсутствие всех 37 служб в launchd. SpringBoard и backboardd имеют `runs = 1` во всех замерах; домашний экран отображается. После включения служб заключительная контрольная загрузка прошла штатно. Тестовый симулятор остановлен; устройство и его данные сохранены для повторения проверки.

Составные группы содержат только найденные в runtime службы из соответствующей группы GoldenNugget. Совместная проверка содержит только 37 найденных служб.

## Ключи без соответствующей launchd-службы

Эти ключи не получили положительного или отрицательного вердикта о загрузке. Среди них `thermalmonitord`, OTA и многие аппаратные/аналитические службы. `com.apple.logd.admin`, `com.apple.logd.events`, `com.apple.spotlight.IndexAgent`, `com.apple.system.logger` найдены как XPC-точки, но не отдельные launchd-службы.

- `com.apple.DuetHeuristic-BM`
- `com.apple.DuetHeuristic-BM.Baseband`
- `com.apple.DumpBasebandCrash`
- `com.apple.DumpPanic`
- `com.apple.MobileInternetSharing`
- `com.apple.OTACrashCopier`
- `com.apple.OTATaskingAgent`
- `com.apple.ProxiedCrashCopier`
- `com.apple.ProxiedCrashCopier.ProxyingDevice`
- `com.apple.ReportCrash`
- `com.apple.ReportCrash.Jetsam`
- `com.apple.ReportMemoryException`
- `com.apple.ReportSystemMemory`
- `com.apple.StatisticalDiagnosticService`
- `com.apple.adprivacyd`
- `com.apple.adservicesd`
- `com.apple.airplay`
- `com.apple.analyticsd`
- `com.apple.analyticsd.admin`
- `com.apple.analyticsd.events`
- `com.apple.atc.atwakeup`
- `com.apple.audioanalyticsd`
- `com.apple.coreduetd`
- `com.apple.crash_mover`
- `com.apple.crashreportcopymobile`
- `com.apple.decisiond`
- `com.apple.diagnosticservicesd`
- `com.apple.diagnosticspushd`
- `com.apple.duetexpertd`
- `com.apple.ecosystemanalyticsd`
- `com.apple.familynotificationd`
- `com.apple.gamekitservice`
- `com.apple.hangreporter`
- `com.apple.hangtracerd`
- `com.apple.insightd`
- `com.apple.logd.admin`
- `com.apple.logd.events`
- `com.apple.logd.watchdog`
- `com.apple.logd_reporter.report_statistics`
- `com.apple.metricsd`
- `com.apple.mobile.NRDUpdated`
- `com.apple.mobile.softwareupdated`
- `com.apple.mocksynclocationd`
- `com.apple.nanomediacontrold`
- `com.apple.nanopreferencesd`
- `com.apple.pluginkit.pkreporter`
- `com.apple.printd`
- `com.apple.promotedcontentd`
- `com.apple.racoon`
- `com.apple.reminderd`
- `com.apple.settings-statsd`
- `com.apple.sidecarcore`
- `com.apple.signpost.signpost_reporter`
- `com.apple.sociald`
- `com.apple.softwareupdateservicesd`
- `com.apple.speechrecognition`
- `com.apple.spindump`
- `com.apple.spotlight.IndexAgent`
- `com.apple.symptomsd`
- `com.apple.symptomsd-app`
- `com.apple.symptomsd-diag`
- `com.apple.sysdiagnose`
- `com.apple.sysdiagnose.darwinos`
- `com.apple.sysdiagnose_helper`
- `com.apple.system.logger`
- `com.apple.tailspind`
- `com.apple.thermalmonitord`
- `com.apple.translated`
- `com.apple.wapic`
- `com.apple.webbookmarksd`
- `com.apple.wifi.wapic`
- `com.apple.wifianalyticsd`
- `com.apple.wifilogd`
- `com.apple.wirelessdiagnostics`

## Артефакты

- [Инвентаризация](inventory.json): все 58 групп, 111 ключей и фактические домены 37 служб.
- [Результаты случаев](results.json).
- В подпапке каждого случая: `result.json`, `bootstatus.txt`, `*-disabled.txt`, `screen.png`.
- В корне: исходные дампы доменов launchd до отключений.
- Скрипт проверки: `tools/audit_simulator_daemons.py` в корне репозитория.
