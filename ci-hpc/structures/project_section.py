#!/usr/bin/python
# author: Jan Hybs


from structures.project_step import ProjectStep


class ProjectSection(object):
    """
    Simple class holding steps together
    :type steps: list[ProjectStep]
    """

    def __init__(self, name, items):
        """
        :type items: list[dict]
        """
        super(ProjectSection, self).__init__()
        self.name = name
        self.steps = list()
        if items:
            for step in items:
                self.steps.append(ProjectStep(self, **step))

    def __iter__(self):
        return iter(self.steps)

    def index(self, o):
        return self.steps.index(o)

    @property
    def ord_name(self):
        return '%d.%s' % (1 if self.name == 'install' else 2, self.name)
