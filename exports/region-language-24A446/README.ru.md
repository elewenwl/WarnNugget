# Region & Language — Experimental 24A446

Формат .batter v3 для GoldenNugget с Community Tweaks. Исследовано только
статически на iOS 27.0.1, build 24A446. На устройстве не проверялось.
Пакеты ограничены версией 27.0.1; формат не умеет ограничивать точный build.

## Использование

1. Импортируйте RegionLanguage-Experimental-24A446.batter в Templates.
2. Откройте переключатели шаблона и выберите нужную операцию.
3. NICKEL требует включённого protective backup без шифрования.
4. Примените изменения обычным способом. Все операции исходно выключены.

## Содержимое

- NICKEL: архив с overrideMap {29: EligibilityOverrideData(answer=4)}.
  Подтверждён потребитель записи звонков, но не принятие нового payload
  eligibilityd. Другие проверки функции (устройство, server bag, MDM и т.д.)
  остаются. Это кандидат для тестирования, не обещание разблокировки.
- IncludeHiddenCallTranslationLocales=true: исследовательский ключ.
  В найденном пути требуется MobileGestalt InternalBuild. Обычный и скрытый
  списки совпадают. Русский язык не добавляется.
- IncludeAIOnlyLanguagesInAllTasks=true: исследовательский ключ.
  Уже true по умолчанию; полезность возможна только при существующем false.

Для Translation используется ManagedPreferences/mobile/com.apple.translationd.
Preferences domain предположен по daemon; runtime-чтение из этого домена не
подтверждено. Эти записи намеренно названы исследовательскими, не unlock.

NICKEL записывается через поддерживаемое path mapping:
/var/containers/Data/SystemGroup/com.apple.eligibilityd/Library/Caches/NeverRestore/eligibility_overrides.data
→ SysContainerDomain-com.apple.eligibilityd / Library/Caches/NeverRestore/eligibility_overrides.data,
owner/group 0. Это логический путь формата GoldenNugget, не доказанный физический
UUID-путь system container на устройстве. Архив сгенерирован с NSKeyedArchive UID
и классами из существующего payload Project Linwood. Offline-декодирование
проверено; Foundation/eligibilityd-unarchive и применение на устройстве — нет.

## Откат и взаимодействие

NICKEL ЗАМЕНЯЕТ весь файл overrides: существующие Siri AI и другие overrides
не сохраняются. В новом payload только домен 29; чужие домены не активируются.
Выключение переключателя отменяет будущую запись, но не откатывает применённую.
Для очистки импортируйте RegionLanguage-Reset-24A446.batter и выберите нужную
операцию. Clear eligibility очищает ВСЕ overrides, не восстанавливает прежние.
Translation reset пишет найденные defaults false/true, не удаляет ключи.
Не применяйте enable и соответствующий reset одновременно; importer обнаруживает
конфликт несовпадающих raw payloads для одного файла.

FOUNDATION_MODELS, PERSONAL_QA, SIRI_WITH_APP_INTENTS, PODCASTS_TRANSCRIPTS и
FORCED_SHUTTER_SOUND оставлены в отчёте: пока установлены только имена/ID.
Подписанный forcedWaitlistStatus также не включён: рабочий payload не получен.

Смотрите research/REPORT.ru.md и evidence в этом архиве.

Источник структуры eligibility archive: mattisklein/project-linwood,
commit b9438cec65b384974a9c6be6169ec9fa1e64c83a, MIT.
https://github.com/mattisklein/project-linwood
Лицензия и исходная памятка включены в attribution/.
