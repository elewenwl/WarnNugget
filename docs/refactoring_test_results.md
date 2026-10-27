# Результаты проверки рефакторинга

24 октября 2026. Python 3.15.0, macOS, Qt offline tests.

Команда: `python3 tools/run_tests.py --report-dir /tmp/gn-refactor-release-check --timeout 180`.

Прошли **60 из 60 наборов**, включая **31 проверку** в новом `test_refactoring_regressions`. AFC, recovery, snapshots, presets, autosave и GUI проверялись без подключённого устройства. USB-передача, полный apply на устройстве и frozen build не проверялись.

`git diff --check` завершился без ошибок.

## Offline tests: 60/60 suites passed

| Suite | Result | Seconds |
| --- | --- | ---: |
| test_active_issues | PASS | 12.3 |
| test_afc_media_safety | PASS | 4.6 |
| test_afc_regressions | PASS | 2.1 |
| test_annotation_imports | PASS | 2.3 |
| test_app_list_export | PASS | 3.4 |
| test_apply_history | PASS | 0.7 |
| test_apply_preview | PASS | 6.6 |
| test_autosave_option | PASS | 2.0 |
| test_awesomeui | PASS | 28.1 |
| test_cache_placement | PASS | 5.9 |
| test_community_tweaks | PASS | 13.8 |
| test_conflicts_and_presets | PASS | 5.9 |
| test_connection_help | PASS | 12.2 |
| test_crash_notify | PASS | 1.1 |
| test_daemons_reveal | PASS | 8.2 |
| test_device_error_classification | PASS | 0.8 |
| test_device_link_shim | PASS | 3.1 |
| test_device_support | PASS | 1.8 |
| test_device_twin | PASS | 10.2 |
| test_eta | PASS | 0.5 |
| test_favorites_settings_search | PASS | 23.0 |
| test_feature_artwork | PASS | 1.7 |
| test_hotload_authority | PASS | 6.0 |
| test_inject_ownership | PASS | 2.6 |
| test_inject_routing | PASS | 2.3 |
| test_interface_picker | PASS | 19.9 |
| test_language_restart | PASS | 3.7 |
| test_lazy_imports | PASS | 4.1 |
| test_light_theme | PASS | 45.7 |
| test_linux_deps | PASS | 0.6 |
| test_log_viewer | PASS | 9.0 |
| test_log_viewer_live | PASS | 13.5 |
| test_operation_result | PASS | 4.5 |
| test_passcode_support | PASS | 0.9 |
| test_performance_regressions | PASS | 10.6 |
| test_portable_and_inspection | PASS | 9.1 |
| test_posterboard_backup_space | PASS | 5.0 |
| test_posterboard_converter | PASS | 0.7 |
| test_posterboard_plist_id | PASS | 0.7 |
| test_posterboard_rebuild | PASS | 0.9 |
| test_posterboard_reset_db | PASS | 1.0 |
| test_posterboard_snapshot | PASS | 5.8 |
| test_preset_catalog | PASS | 24.5 |
| test_protective_cache | PASS | 4.0 |
| test_protective_filters | PASS | 3.4 |
| test_refactoring_regressions | PASS | 10.6 |
| test_repair_regressions | PASS | 8.1 |
| test_reset_no_capture | PASS | 8.9 |
| test_restore_progress | PASS | 13.1 |
| test_restore_reconnect | PASS | 4.3 |
| test_risk_and_share | PASS | 10.8 |
| test_siri_ai | PASS | 8.3 |
| test_sparse_backup_format | PASS | 0.4 |
| test_statusbar_archive | PASS | 0.4 |
| test_statusbar_fetch | PASS | 7.7 |
| test_statusbar_preview | PASS | 3.1 |
| test_storage | PASS | 0.4 |
| test_template_options | PASS | 2.2 |
| test_tendie_convert | PASS | 3.1 |
| test_ui_refinements | PASS | 12.1 |
