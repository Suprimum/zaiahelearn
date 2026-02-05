from django.apps import AppConfig
from django.conf import settings


class CoursesConfig(AppConfig):
    name = f'{settings.PROJECT_NAME}.apps.courses'

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)

        self.default_auto_field = 'django.db.models.BigAutoField'
        self.default_app_config = f'{settings.PROJECT_NAME}.apps.courses.apps.CoursesConfig'

    def ready(self):
        import zaiahelearn.apps.courses.signals  # noqa: F401

        return super().ready()
