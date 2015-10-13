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
from openerp.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = "product.product"

    average_consumption = fields.Float(
        compute='_average_consumption',
        string='Average Consumption per day')
    total_consumption = fields.Float(
        compute='_average_consumption',
        string='Total Consumption')
    nb_days = fields.Float(
        compute='_average_consumption',
        string='Number of days for the calculation',
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

    @api.multi
    def _average_consumption(self):
        self.refresh()
        product_ids = map(lambda p: p.id, self)
        first_date = time.strftime('%Y-%m-%d')
        begin_date = (
            datetime.datetime.today()
            - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        ctx = dict(self.env.context)
        ctx.update({
            'from_date': begin_date
        })
        domain_products = [('product_id', 'in', product_ids)]
        domain_move_out = []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
            self._get_domain_locations()
        domain_move_out += self.with_context(ctx)._get_domain_dates() \
            + [('state', 'in', ('confirmed', 'waiting', 'assigned', 'done'))] \
            + domain_products
        domain_move_out += domain_move_out_loc
        moves_out = self.env['stock.move'].read_group(
            domain_move_out, ['product_id', 'product_qty'], ['product_id'])
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']),
                             moves_out))
        for product in self:
            qty_out = float_round(
                moves_out.get(product.id, 0.0),
                precision_rounding=product.uom_id.rounding)
            first_date = max(begin_date, product.with_context(ctx)._min_date())
            nb_days = (
                datetime.datetime.today()
                - datetime.datetime.strptime(first_date, '%Y-%m-%d')
            ).days
            product.average_consumption = (
                nb_days and - qty_out / nb_days or 0.0)
            product.total_consumption = - qty_out or 0.0
            product.nb_days = nb_days or 0.0
        return True
