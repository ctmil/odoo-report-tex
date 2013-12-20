# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Moldeo Interactive SA (http://moldeo.coop)
# All Right Reserved
#
# Author : Cristian S. Rocha (Moldeo Interactive)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

import subprocess
import os
import sys
from openerp import report
import tempfile
import time
import logging
import shutil

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from openerp import netsvc
from openerp import pooler
from openerp.report.report_sxw import *
from openerp import addons
from openerp import tools
from openerp.tools.translate import _
from openerp.osv.osv import except_osv

from report_helper import LatexHelper

_logger = logging.getLogger(__name__)

def mako_template(text):
    """Build a Mako template.

    This template uses UTF-8 encoding
    """
    tmp_lookup  = TemplateLookup() #we need it in order to allow inclusion and inheritance
    return Template(text, input_encoding='utf-8', output_encoding='utf-8', lookup=tmp_lookup)

class LatexParser(report_sxw):
    """Custom class that use latexpdf to render PDF reports
       Code partially taken from report latex. Thanks guys :)
    """
    def __init__(self, name, table, rml=False, parser=False,
        header=True, store=False):
        self.parser_instance = False
        self.localcontext = {}
        report_sxw.__init__(self, name, table, rml, parser,
            header, store)

    def get_lib(self, cursor, uid):
        """Return the pdflatex path"""
        proxy = self.pool.get('ir.config_parameter')
        pdflatex_path = proxy.get_param(cursor, uid, 'pdflatex_path')

        if not pdflatex_path:
            try:
                defpath = os.environ.get('PATH', os.defpath).split(os.pathsep)
                if hasattr(sys, 'frozen'):
                    defpath.append(os.getcwd())
                    if tools.config['root_path']:
                        defpath.append(os.path.dirname(tools.config['root_path']))
                pdflatex_path = tools.which('pdflatex', path=os.pathsep.join(defpath))
            except IOError:
                pdflatex_path = None

        if pdflatex_path:
            return pdflatex_path

        raise except_osv(
                         _('pdflatex executable path is not set'),
                         _('Please install executable on your system' \
                         ' (sudo apt-get install texlive-latex-base)')
                        )

    def generate_pdf(self, comm_path, report_xml, tex, resource_path=None):
        """Call latex in order to generate pdf"""
        tmp_dir = tempfile.mkdtemp()
        if comm_path:
            command = [comm_path]
        else:
            command = ['pdflatex']
        command.extend(['-output-directory', tmp_dir])
        command.extend(['-interaction', 'batchmode'])

        count = 0

        prefix_filename = str(time.time()) + str(count)
        tex_filename = prefix_filename +'.tex'
        pdf_filename = prefix_filename +'.pdf'
        log_filename = prefix_filename +'.log'
        tex_file = file(os.path.join(tmp_dir, tex_filename), 'w')
        count += 1
        tex_file.write(tex)
        tex_file.close()
        command.append(tex_filename)

        env = os.environ
        if resource_path:
            env.update(dict(TEXINPUTS="%s:" % resource_path))

        _logger.info("Environment Variables: %s" % env)

        stderr_fd, stderr_path = tempfile.mkstemp(dir=tmp_dir,text=True)
        try:
            status = subprocess.call(command, stderr=stderr_fd, env=env)

            # Try to rerun if errors happens
            if status:
                _logger.info("pdflatex return %i. Try rerun." % status)
                status = subprocess.call(command, stderr=stderr_fd, env=env)

            if status:
                import pdb; pdb.set_trace()

            os.close(stderr_fd) # ensure flush before reading
            stderr_fd = None # avoid closing again in finally block
            fobj = open(stderr_path, 'r')
            error_message = fobj.read()
            fobj.close()
            if not error_message:
                error_message = _('No diagnosis message was provided')
            else:
                error_message = _('The following diagnosis message was provided:\n') + error_message
            if status :
                raise except_osv(_('Latex error' ),
                                 _("The command 'pdflatex' failed with error code = %s. Message: %s") % (status, error_message))
            pdf_file = open(os.path.join(tmp_dir, pdf_filename), 'rb')
            pdf = pdf_file.read()
            pdf_file.close()
        finally:
            if stderr_fd is not None:
                os.close(stderr_fd)
            try:
                shutil.rmtree(tmp_dir)
            except (OSError, IOError), exc:
                _logger.error('cannot remove dir %s: %s', tmp_dir, exc)
        return pdf

    def translate_call(self, src):
        """Translate String."""
        ir_translation = self.pool.get('ir.translation')
        name = self.tmpl and 'addons/' + self.tmpl or None
        res = ir_translation._get_source(self.parser_instance.cr, self.parser_instance.uid,
                                         name, 'report', self.parser_instance.localcontext.get('lang', 'en_US'), src)
        if res == src:
            # no translation defined, fallback on None (backward compatibility)
            res = ir_translation._get_source(self.parser_instance.cr, self.parser_instance.uid,
                                             None, 'report', self.parser_instance.localcontext.get('lang', 'en_US'), src)
        if not res :
            return src
        return res

    # override needed to keep the attachments storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        """generate the PDF"""

        if context is None:
            context={}
        if report_xml.report_type != 'latex':
            return super(LatexParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)

        self.parser_instance = self.parser(cursor,
                                           uid,
                                           self.name2,
                                           context=context)

        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        self.parser_instance.set_context(objs, data, ids, report_xml.report_type)

        template =  False
        resource_path = None

        if report_xml.report_file :
            # backward-compatible if path in Windows format
            report_path = report_xml.report_file.replace("\\", "/")
            path = addons.get_module_resource(*report_path.split('/'))
            resource_path = os.path.dirname(path)
            if path and os.path.exists(path) :
                template = file(path).read()
        if not template :
            raise except_osv(_('Error!'), _('Latex report template not found!'))

        body_mako_tpl = mako_template(template)
        helper = LatexHelper(cursor, uid, report_xml.id, context)
        try :
            tex = body_mako_tpl.render(helper=helper,
                                        _=self.translate_call,
                                        **self.parser_instance.localcontext)
        except Exception:
            msg = exceptions.text_error_template().render()
            _logger.error(msg)
            raise except_osv(_('Latex render!'), msg)
        bin = self.get_lib(cursor, uid)
        pdf = self.generate_pdf(bin, report_xml, tex, resource_path=resource_path)
        return (pdf, 'pdf')


    def create(self, cursor, uid, ids, data, context=None):
        """We override the create function in order to handle generator
           Code taken from report openoffice. Thanks guys :) """
        pool = pooler.get_pool(cursor.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cursor, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:

            report_xml = ir_obj.browse(cursor,
                                       uid,
                                       report_xml_ids[0],
                                       context=context)
            report_xml.report_rml = None
            report_xml.report_rml_content = None
            report_xml.report_sxw_content_data = None
            report_xml.report_sxw_content = None
            report_xml.report_sxw = None
        else:
            return super(LatexParser, self).create(cursor, uid, ids, data, context)
        if report_xml.report_type != 'latex' :
            return super(LatexParser, self).create(cursor, uid, ids, data, context)
        result = self.create_source_pdf(cursor, uid, ids, data, report_xml, context)
        if not result:
            return (False,False)
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
