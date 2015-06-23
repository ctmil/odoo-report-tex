# -*- coding: utf-8 -*-

from openerp import models, fields, report, addons
from latex_report import LatexParser


class ir_actions_report_xml(models.Model):
    _inherit = 'ir.actions.report.xml'

    report_type = fields.Selection(selection_add=[("tex", "Tex")])

    def _lookup_report(self, cr, name):
        """
        Look up a report definition.
        """
        import operator
        import os
        opj = os.path.join

        if 'report.' + name in report.interface.report_int._reports:
            new_report = report.interface.report_int._reports['report.' + name]
            if not isinstance(new_report, LatexParser):
                new_report = None
        else:
            cr.execute("SELECT * FROM ir_act_report_xml"
                       " WHERE report_name=%s and report_type=%s",
                       (name, 'tex'))
            r = cr.dictfetchone()
            if r:
                if r['parser']:
                    parser = operator.attrgetter(r['parser'])(addons)
                    kwargs = {'parser': parser}
                else:
                    kwargs = {}

                new_report = LatexParser('report.'+r['report_name'],
                                         r['model'],
                                         opj('addons', r['report_file'] or '/'),
                                         header=r['header'],
                                         register=False, **kwargs)
            else:
                new_report = None

        if new_report:
            return new_report
        else:
            return super(ir_actions_report_xml, self)._lookup_report(cr, name)

ir_actions_report_xml()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
