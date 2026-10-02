from django.apps import AppConfig


class RdgeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rdgenerator'

    def ready(self):
        # Django 6.1 refuses to talk to MySQL older than 8.4. The gate lives in
        # django/db/backends/base/base.py:check_database_version_supported(),
        # and the only thing driving it is DatabaseFeatures.minimum_database_version
        # (see django/db/backends/mysql/features.py), so lowering that value is
        # enough to let MySQL 8.0 through.
        #
        # This is a deliberate escape hatch for installs still running MySQL 8.0.
        # Remove it once the server is on 8.4+. Note that it also lowers the
        # MariaDB floor -- restore (10, 11) there if you ever switch to MariaDB.
        from django.conf import settings

        if not any(
            cfg.get('ENGINE', '').endswith('.mysql')
            for cfg in settings.DATABASES.values()
        ):
            return

        # mysql/features.py imports no driver, so patching it cannot fail just
        # because MySQLdb/PyMySQL is missing.
        from django.db.backends.mysql.features import DatabaseFeatures

        DatabaseFeatures.minimum_database_version = (8, 0, 11)
