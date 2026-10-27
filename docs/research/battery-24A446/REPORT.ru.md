# Кандидаты на экономию батареи для GoldenNugget

Дата: 23 октября 2026. Проверенная прошивка: iOS 27.0.1, 24A446,
iPhone15,4 (iPhone 15). Инструмент: ipsw 3.1.738. Идентификаторы —
в `identity.json`; листинги сохранены рядом с отчётом.

Найдены три новых для текущего реестра GoldenNugget настройки с подтверждённым
путём записи preferences и один кандидат ограничения частоты экрана.
Это существующие механизмы iOS, новые именно для проекта.
Уточнение: все четыре возможности уже представлены в штатном разделе
«Универсальный доступ → Движение». Autoplay имеет отдельные переключатели;
не следует считать, что один Reduce Motion обязательно выключает их все.
В качестве поиска скрытых батарейных твиков эти находки не дают новых функций:
они лишь позволяют потенциально включать штатные настройки из пресета.
Экономия энергии предполагается по уменьшению работы; её величина не измерена.
Применение через restore/managed preferences на физическом устройстве не проверялось.
При исследовании код приложения и настройки устройств не менялись.
По последующему запросу добавлен экспериментальный `LimitDisplayRefreshRate`
в Internal Options для iOS 27+: managed `com.apple.Accessibility`, bool true/false.
Нетронутый переключатель не пишет preference; выключение после включения
пишет false. Проверены генерация plist и регистрация в общем реестре.
Применение на физическом устройстве по-прежнему не проверено; конечный storage
AXSettings и работа managed override остаются неподтверждёнными.

## Приоритетные кандидаты

| Возможность | Ключ и предлагаемое значение | Что подтверждено | Практический предел |
|---|---|---|---|
| Остановить автоматическое проигрывание GIF/анимированных изображений | `ReduceMotionAutoplayAnimatedImagesEnabled = 0` | getter, setter, ключ и домен | Действует там, где приложение учитывает системную настройку; не гарантирует остановку любого GIF в любом приложении |
| Остановить автоматическое проигрывание видеопревью | `ReduceMotionAutoplayVideoPreviewsEnabled = 0` | setter нормализует значение к 0/1 и пишет числовую preference | Не является общесистемным запретом любого видео; приложение может иметь собственный механизм autoplay |
| Остановить автоматические эффекты iMessage | `ReduceMotionAutoplayMessagesEffectsEnabled = 0` | setter, ключ и домен | Польза зависит от частоты использования эффектов; ожидается небольшой вклад |
| Ограничивать частоту экрана без полного Low Power Mode | `LimitDisplayRefreshRate` — кандидат, точный формат хранения ещё требует проверки | Настройка создаётся в AXSettings с булевым значением по умолчанию false | Только модели ProMotion; не путать с `LimitFrameRate`, который здесь является идентификатором capability |

Первые три ключа относятся к `com.apple.Accessibility`.
Штатная запись использует CFPreferences для текущего пользователя и AnyHost;
обычный пользовательский файл ожидается в
`/var/mobile/Library/Preferences/com.apple.Accessibility.plist`.
Путь GoldenNugget `FileLocation.accessibility` указывает на **managed** файл
`/var/Managed Preferences/mobile/com.apple.Accessibility.plist`.
Работа именно этого канала для найденных ключей остаётся отдельной проверкой.
Нельзя заменять пользовательский plist целиком: в нём находятся другие настройки доступности.

Apple документирует штатные переключатели автопроигрывания и ограничение
ProMotion до 60 кадров/с: [Customize onscreen motion](https://support.apple.com/en-ae/guide/iphone/iph0b691d3ed/ios).
Документация подтверждает назначение функций, но не даёт процента экономии для этих твиков.

## Проверяемые доказательства

`constants.txt` связывает экспортированные переменные ключей с CFString:

- `0x1e4523e70` → `0x1ea0b3738` → `ReduceMotionAutoplayAnimatedImagesEnabled`;
- `0x1e4523e80` → `0x1ea0b3778` → `ReduceMotionAutoplayMessagesEffectsEnabled`;
- `0x1e4523e88` → `0x1ea0b3798` → `ReduceMotionAutoplayVideoPreviewsEnabled`;
- `0x1e4523790` → `0x1ea0b1bb8` → `com.apple.Accessibility`.

В `/usr/lib/libAccessibility.dylib`:

- `__AXSSetReduceMotionAutoplayAnimatedImagesEnabled`, `0x18f80a77c`:
  загружает соответствующий ключ и вызывает `__setPreferenceAppWithNotification`;
- `__AXSSetReduceMotionAutoplayMessagesEffectsEnabled`, `0x18f80a9dc`:
  тот же путь записи;
- `__AXSSetReduceMotionAutoplayVideoPreviewsEnabled`, `0x18f80add0`:
  приводит аргумент к 0/1 и вызывает `__setNumberPreferenceApp` с числовым типом 9;
- `__setPreferenceAppWithNotification`, `0x18f7eb6e4`:
  при отсутствии app-specific домена выбирает `_kAXSAccessibilityPreferenceDomain`
  (`0x18f7eb8f4–0x18f7eb900`); путь записи содержит
  `CFPreferencesSetValue` (`0x18f7eb9e0`) с CurrentUser/AnyHost.
  Также видны обращения к BackBoard для изменения preferences от имени mobile.

В `AccessibilityUtilities.framework` функция `0x189dc2ab0` создаёт
AXSettings-настройку `LimitDisplayRefreshRate` (строка используется по адресу
`0x189dc2bb0`). Этот листинг **не устанавливает** конечный plist-путь,
переносимость между iOS 26/27 или работоспособность managed override.

## Что не считать готовым батарейным твиком

**DisableLiveActivities / DisableTimelines / DisableSnapshots.**
Строки существуют в `ChronoServices.framework`, используются при создании
preferences в `sub_18c06cdd4`, домен рядом — `com.apple.chronod`.
Однако перед созданием каждой настройки вызывается
`os_variant_has_internal_ui("com.apple.chrono")`; результат передаётся
в общий конструктор `0x18c06756c` через x6.
Назначение этого аргумента до конечного чтения полностью не прослежено.
Это зависимость от внутреннего режима, которую нужно разрешить до рекомендации
на обычной iOS; утверждать по одним строкам, что флаги работают, нельзя.
Отключение snapshots, кроме того, не эквивалентно отключению фоновых обновлений.
Apple уже ограничивает обновления виджетов бюджетом ради батареи:
[Keeping a widget up to date](https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date).

**Постоянный LPM / снятие ограничения 60 Гц в LPM / Adaptive Power на неподдерживаемых моделях.**
В исследованных LowPowerMode и PowerExperience обнаружены клиентские XPC-пути
к `powerd`/`powerexperienced`; готовый plist override с доказанным чтением
не установлен. Наличие класса или XPC-метода не означает возможность реализации
через файловый restore GoldenNugget. [Штатный LPM](https://support.apple.com/en-euro/101604)
изменяет сразу несколько функций, включая частоту ProMotion и фоновые обновления.

**Отключение thermalmonitord, powerd, dasd и других системных служб.**
В этом исследовании нет доказательств положительного энергетического результата
от их отключения. Существующие переключатели демонов в проекте не являются
доказательством экономии и не включены в список новых кандидатов.

## Следующий этап перед добавлением в приложение

Начать с трёх autoplay-настроек: снять исходные значения, проверить каждый
managed override отдельно, перезагрузить, подтвердить изменение поведения,
восстановить исходное состояние. Отдельно проверить числовой тип значения,
зависимости от Reduce Motion и переопределений для конкретных приложений.
Для 60 Гц сначала установить фактический storage-путь AXSettings и устройство
с ProMotion: исследованный iPhone15,4 имеет экран 60 Гц и не подходит для такого A/B.

Энергетические измерения нужны отдельно: одинаковые яркость, сеть, температура
и сценарий, повторные прогоны. Результат этого прохода — подтверждённые
статические кандидаты, а не измеренное увеличение автономности.

## Воспроизведение

Использовать основной DSC вместе со всеми его subcache-файлами:

```sh
ipsw dyld macho <DSC> /usr/lib/libAccessibility.dylib --symbols --strings --no-color
ipsw dyld disass <DSC> --vaddr 0x18f80a77c --count 70 --no-color
ipsw dyld disass <DSC> --vaddr 0x18f80add0 --count 45 --no-color
ipsw dyld disass <DSC> --vaddr 0x18f80a9dc --count 40 --no-color
ipsw dyld disass <DSC> --vaddr 0x18f7eb6e4 --count 330 --no-color
ipsw dyld dump <DSC> 0x1e4523e70 --count 4 --addr
ipsw dyld dump <DSC> 0x1e4523790 --count 1 --addr
ipsw dyld disass <DSC> --vaddr 0x189dc2ab0 --count 140 --no-color
ipsw dyld disass <DSC> --vaddr 0x18c06cdd4 --count 850 --no-color
```

Адреса относятся только к 24A446. В этом проходе также выполнен ограниченный
поиск строк/символов в PowerUI, PowerExperience, BatteryIntelligence,
CoreBrightness, DuetActivityScheduler и BackgroundTaskAgent. Это не полный
аудит iOS. REA MCP в сессии отсутствовал; все доказательства получены обычным
CLI ipsw, без REA Evidence IDs и без выполнения кода прошивки.
