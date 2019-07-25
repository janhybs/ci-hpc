#!/usr/bin/python
# author: Jan Hybs


class ProjectSection(object):
    """
    Simple class holding steps together
    :type steps: list[ProjectStep]
    """

    def __init__(self, name, items):
        """
        :type items: list[dict]
        """
        from cihpc.core.structures.project_step import ProjectStep

        super(ProjectSection, self).__init__()
        self.name = name
        self.steps = list()
        if items:
            for step in items:
                self.steps.append(ProjectStep(self, **step))

    def __len__(self):
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps)

    @property
    def pretty(self):
        lines = [
            'ProjectSection <{self.name}> %d item(s)' % len(self),
            '  - items:'
        ]
        lines.extend(['    - ProjectStep <{step.name}>'.format(step=step) for step in self])
        return '\n'.join(lines).format(self=self)

    def index(self, o):
        return self.steps.index(o)

    @property
    def ord_name(self):
        return '%d.%s' % (1 if self.name == 'install' else 2, self.name)
