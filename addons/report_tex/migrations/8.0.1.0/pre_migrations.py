# -*- encoding: utf-8 -*-

from openerp.openupgrade import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.update_module_names(cr, ('report_latex', 'report_tex'))
    import pdb; pdb.set_trace()
    pass
