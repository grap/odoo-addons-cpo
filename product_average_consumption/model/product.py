# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Average Consumption Module for Odoo
#    Copyright (C) 2013-2014 GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.tools.translate import _


class product_product(Model):
    _inherit = "product.product"

    def _min_date(self, cr, uid, product_id, context=None):
        query = """SELECT to_char(min(date), 'YYYY-MM-DD') \
                from stock_move where product_id = %s""" % (product_id)
        cr.execute(query)
        results = cr.fetchall()
        return results and results[0] and results[0][0] \
                or time.strftime('%Y-%m-%d')

    def _average_consumption(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        stock_move_obj = self.pool.get('stock.move')
        total_consumption = 0
        first_date = time.strftime('%Y-%m-%d')
        begin_date = (datetime.datetime.today()
                    - datetime.timedelta(days=365))\
                    .strftime('%Y-%m-%d')

        if context is None:
            context = {}
        c = context.copy()
        c.update({
            'states': ('confirmed', 'waiting', 'assigned', 'done'),
            'what': ('out', ),
            'from_date': begin_date
            })
        stock = self.get_product_available(cr, uid, ids, context=c)

        for product in self.browse(cr, uid, ids, context=context):
            first_date = max(
                begin_date,
                self._min_date(cr, uid, product.id, context=c)
                )
            nb_days = (
                    datetime.datetime.today()
                    - datetime.datetime.strptime(first_date, '%Y-%m-%d')
                    ).days
            result[product.id] = {
                'average_consumption': nb_days
                                    and - stock[product.id] / nb_days
                                    or False,
                'total_consumption': - stock[product.id] or False,
                'nb_days': nb_days or False,
            }
        return result

    _columns = {
        'average_consumption': fields.function(_average_consumption,
            type='float', string='Average Consumption per day',
            multi="average_consumption"),
        'total_consumption': fields.function(_average_consumption,
            type='float', string='Total Consumption',
            multi="average_consumption"),
        'nb_days': fields.function(_average_consumption,
            type='float', string='Number of days for the calculation',
            multi="average_consumption",
            help="The calculation will be done for the last 365 days or since \
            the first purchase or sale of the product if it's more recent"),
    }
