import os
import tempfile
import requests
import shutil
import tarfile
import re


class ReleaseHandler(object):
    version_filenames = {
        "govuk_template": "VERSION",
        "digital_marketplace_frontend_toolkit": "VERSION.txt"
    }
    local_release_dirs = {
        "govuk_template": "govuk_template",
        "digital_marketplace_frontend_toolkit":
            "digital_marketplace_frontend_toolkit"
    }
    release_urls = {
        "govuk_template":
            "https://github.com/alphagov/govuk_template/releases/download"
            "/v{0}/jinja_govuk_template-{0}.tgz",
        "digital_marketplace_frontend_toolkit":
            "https://github.com/alphagov/digitalmarketplace-frontend-toolkit/"
            "archive/v{0}.tar.gz"
    }
    release_archives = {
        "govuk_template": "jinja_govuk_template-{0}.tgz",
        "digital_marketplace_frontend_toolkit":
            "digitalmarketplace-frontend-toolkit-{0}.tar.gz"
    }

    def __init__(self, release_name, version):
        self.release_name = release_name
        self.required_version = version
        self.repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".."))
        self.local_release_dir = os.path.join(self.repo_root,
                                              self.get_local_release_dir(
                                                  release_name))

        self.required_release_url = self.get_release_url(release_name).format(
            self.required_version)
        self.required_release_filename = self.get_release_archive(
            release_name).format(self.required_version)
        self.required_release_dirname = re.sub(
            r'([a-z0-9\._-]+)(\.tgz|\.tar\.gz)$', r'\1',
            self.required_release_filename)

    def needs_update(self):
        current_version = self.get_current_version()
        if current_version is False:
            print("No existing release for %s" % self.release_name)
            return True
        elif current_version != self.required_version:
            print("updating %s to required version" % self.release_name)
            return True
        else:
            print("%s matches required version; exiting" % self.release_name)
            return False

    def get_release_archive(self, release_name):
        archive = self.release_archives.get(release_name)
        if archive is None:
            raise LookupError("Release name %s not recognised" % release_name)
        else:
            return archive

    def get_release_url(self, release_name):
        url = self.release_urls.get(release_name)
        if url is None:
            raise LookupError("Release name %s not recognised" % release_name)
        else:
            return url

    def get_local_release_dir(self, release_name):
        local_dir = self.local_release_dirs.get(release_name)
        if local_dir is None:
            raise LookupError("Release name %s not recognised" % release_name)
        else:
            return local_dir

    def get_version_filename(self, release_name):
        version_filename = self.version_filenames.get(release_name)
        if version_filename is None:
            raise LookupError("Release name %s not recognised" % release_name)
        else:
            return version_filename

    def get_current_version(self):
        if os.path.isdir(self.local_release_dir):
            version_filename = self.get_version_filename(self.release_name)
            current_version = \
                open(os.path.join(self.local_release_dir, version_filename),
                     "r").read().splitlines()[0]
            return current_version
        else:
            return False

    def get_folder(self):
        return self.template_dir

    def download_archive(self, temp_dir):
        print("Download: %s (%s)" % (self.release_name, self.required_version))
        temp_tarball_filename = os.path.join(temp_dir,
                                             self.required_release_filename)
        response = requests.get(self.required_release_url)
        open(temp_tarball_filename, "wb").write(response.content)

    def extract_archive(self, temp_dir):
        print("Extracting %s (%s) from tarball" % (
            self.release_name, self.required_version))
        tarball = os.path.join(temp_dir, self.required_release_filename)
        tar_obj = tarfile.open(tarball, "r:gz")
        print("Extracting %s into %s" % (
            self.required_release_filename, temp_dir))
        tar_obj.extractall(temp_dir)

    def save_archive(self, temp_dir):
        downloaded_release_dir = os.path.join(temp_dir,
                                              self.required_release_dirname)

        print("Saving the release to the '%s' dir" % self.release_name)
        shutil.rmtree(self.local_release_dir)
        shutil.copytree(downloaded_release_dir, self.local_release_dir)

    def update_release(self):
        temp_dir = tempfile.mkdtemp()

        self.download_archive(temp_dir)
        self.extract_archive(temp_dir)
        self.save_archive(temp_dir)

    def clean_up(self, temp_dir):
        shutil.rmtree(temp_dir)
