# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Average Consumption Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
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
from openerp import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    average_consumption = fields.Float(
        compute='_average_consumption',
        string='Average Consumption per day',
        multi='average_consumption')
    total_consumption = fields.Float(
        compute='_average_consumption',
        string='Total Consumption',
        multi='average_consumption')
    nb_days = fields.Float(
        compute='_average_consumption',
        string='Number of days for the calculation',
        multi='average_consumption',
        help="""The calculation will be done for the last 365 days or"""
        """ since the first purchase or sale of the product if it's"""
        """ more recent""")

    @api.one
    def _min_date(self):
        query = """SELECT to_char(min(date), 'YYYY-MM-DD') \
                from stock_move where product_id = %s""" % (self.id)
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        return results and results[0] and results[0][0] \
            or time.strftime('%Y-%m-%d')

    @api.one
    def _average_consumption(self):
        first_date = time.strftime('%Y-%m-%d')
        begin_date = (
            datetime.datetime.today()
            - datetime.timedelta(days=365)).strftime('%Y-%m-%d')

        ctx = dict(self.env.context)
        ctx.update({
            'states': ('confirmed', 'waiting', 'assigned', 'done'),
            'what': ('out', ),
            'from_date': begin_date
        })
        stock = self.with_context(ctx)._product_available()
        first_date = max(begin_date, self.with_context(ctx)._min_date())
        nb_days = (
            datetime.datetime.today()
            - datetime.datetime.strptime(first_date, '%Y-%m-%d')
        ).days
        self.average_consumption = (
            nb_days and - stock[self.id]['qty_available'] / nb_days or 0.0)
        self.total_consumption = - stock[self.id]['qty_available'] or 0.0
        self.nb_days = nb_days or 0.0
        return True
