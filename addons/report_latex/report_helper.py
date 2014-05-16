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

from openerp import pooler
import cStringIO
import PIL.Image
import base64
import zlib
import tempfile
import os
import os.path
import shutil
import imghdr
import logging

_logger = logging.getLogger(__name__)

img_template = """
{{
\\makebox[{1:0.4}cm][l]{{\\immediate\\pdfliteral{{
  q
  {3} 0 0 {4} 0 0 cm
  {1:0.4} 0 0 {2:0.4} 0 0 cm
  0.885 0 0 0.885 0 0 cm 
  BI
  /W {3} 
  /H {4} 
  /CS /RGB
  /BPC 8
  /F [ /AHx /Fl ]
  ID
  {5}>
  EI
  Q
}}\\vbox to {2:0.4}cm{{}}}}
}}
"""

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

lang_map = {
    'es': 'spanish',
}

class LatexHelper(object):
    """Set of usefull report helper"""
    def __init__(self, cursor, uid, report_id, context):
        "constructor"
        self.cursor = cursor
        self.uid = uid
        self.pool = pooler.get_pool(self.cursor.dbname)
        self.report_id = report_id
        self.fs_images = []
        self.tmp_dir = tempfile.mkdtemp()
        self._lang = None
        if 'lang' in context:
            lang = context['lang'].split('_',1)[0]
            self._lang = lang_map[lang] if lang in lang_map else None

    def __del__(self):
        _logger.debug("Removing temporal directory: %s" % self.tmp_dir)
        shutil.rmtree(self.tmp_dir)

    def putImage(self, image, **args):
        # Put image in storage
        binimg = base64.b64decode(image)
        suffix = imghdr.what('', binimg)
        img_file_fd, img_filename = tempfile.mkstemp(suffix='.%s' % suffix, dir=self.tmp_dir)
        self.fs_images.append(img_file_fd)
        os.write(img_file_fd, binimg)
        os.close(img_file_fd)
        options = ','.join( "%s=%r" % i for i in args.items() )
        return "\includegraphics[%s]{%s}" % (options, os.path.join(self.tmp_dir, img_filename))

    def embedImage(self, image):
        # Reading image from database
        binimg = base64.b64decode(image)
        file_like = cStringIO.StringIO(binimg)
        img = PIL.Image.open(file_like)
        size_px = img.size
        size_cm = map(lambda v: v/28., size_px)

        # Convert image to string
        data = ""
        for y in xrange(size_px[1]):
            for x in xrange(size_px[0]):
                c = img.getpixel((x,y))
                data += chr(c[0])
                data += chr(c[1])
                data += chr(c[2])

        # Compress image string and format it to pdf
        cdata = zlib.compress(data)
        rdata = "\n".join(chunks("".join([ "%02X" % ord(d) for d in cdata ]), 80))

        return img_template.format(0, size_cm[0], size_cm[1], size_px[0], size_px[1], rdata)

    def texescape(self, s):
        s = s.replace("\\","\\\\").replace("%","\\%").replace("$","\\$").replace("{","\\{").replace("}","\\}").replace("\n", "\\\\")
        return s

    def set_language(self):
        return """
               \usepackage[%s]{babel}
               \usepackage[utf8]{inputenc}
               \usepackage[T1]{fontenc}
               """ % (self._lang or 'interlingua')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
