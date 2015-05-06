import yaml
import inflection
import re
import os

from collections import OrderedDict


class QuestionsLoader(object):

    def __init__(self,
                 manifest='questions_manifest.yml',
                 questions_dir=''):

        with open(manifest, "r") as file:
            section_order = yaml.load(file)

        self._directory = questions_dir
        self._question_cache = {}
        self.sections = [
            self._populate_section_(s) for s in section_order
        ]

    def get_section(self, requested_section):

        for section in self.sections:
            if section["id"] == requested_section:
                return section

    def get_question(self, question):

        if question not in self._question_cache:

            question_file = self._directory + question + ".yml"

            if not os.path.isfile(question_file):
                self._question_cache[question] = {}
                return {}

            with open(question_file, "r") as file:
                question_content = yaml.load(file)

            question_content["id"] = question

            # wrong way to do it? question should be shown by default.
            question_content["depends_on_lots"] = (
                self._get_dependent_lots_(question_content["dependsOnLots"])
            ) if "dependsOnLots" in question_content else (
                ["saas", "paas", "iaas", "scs"]
            )

            self._question_cache[question] = question_content

        return self._question_cache[question]

    def _populate_section_(self, section):
        section["questions"] = [
            self.get_question(q) for q in section["questions"]
        ]
        all_dependencies = [
            q["depends_on_lots"] for q in section["questions"]
        ]
        section["depends_on_lots"] = [
            y for x in all_dependencies for y in x  # flatten array
        ]
        section["id"] = self._make_id_(section["name"])
        return section

    def _make_id_(self, name):
        return inflection.underscore(
            re.sub("\s", "_", name)
        )

    def _get_dependent_lots_(self, dependent_lots_as_string):
        return [
            x.strip() for x in dependent_lots_as_string.lower().split(",")
        ]
