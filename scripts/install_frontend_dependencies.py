import sys
from release_handler import ReleaseHandler


class DependenciesHandler(object):
    "Manage the front-end dependencies not handled by NPM"

    dependencies = {
        "govuk_template": "0.12.0",
        "digital_marketplace_frontend_toolkit": "1.0.3"
    }

    # public methods
    def get_release(self, version):
        govuk_template_handler = releaseHandler(version)
        if govuk_template_handler.needs_update():
            govuk_template_handler.update_template()
        return template_handler.get_release()

    def get_digital_marketplace_frontend_toolkit(self):
        template_handler = TemplateHandler()
        if template_handler.needs_update():
            template_handler.update_template()
        return template_handler.get_folder()

    def install_dependency(self, dependency_name):
        version = self.dependencies[dependency_name]
        release_handler = ReleaseHandler(dependency_name, version)
        if release_handler.needs_update():
            release_handler.update_release()

    def install(self):
        for dependency_name in self.dependencies:
            self.install_dependency(dependency_name)


if __name__ == "__main__":
    dependencies_handler = DependenciesHandler()
    dependencies_handler.install()
