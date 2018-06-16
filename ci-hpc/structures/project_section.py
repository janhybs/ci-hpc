#!/usr/bin/python
# author: Jan Hybs


from structures.project_step import ProjectStep


class ProjectSection(list):
    """
    Simple class holding steps together
    """
    def __init__(self, name, items):
        super(ProjectSection, self).__init__()
        self.name = name
        if items:
            for step in items:
                self.append(ProjectStep(**step))

    @property
    def ord_name(self):
        return '%d.%s' % (1 if self.name == 'install' else 2, self.name)