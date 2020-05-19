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
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = "product.product"

    average_consumption = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (max 365 days)')
    total_consumption = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. max 365 days)')
    average_consumption_15 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (15 days)')
    total_consumption_15 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 15 days)')
    average_consumption_30 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (30 days)')
    total_consumption_30 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 30 days)')
    average_consumption_90 = fields.Float(
        compute='_average_consumption',
        string='Average Consumption (90 days)')
    total_consumption_90 = fields.Float(
        compute='_average_consumption',
        string='Total Consumption (ud. 90 days)')
    nb_days = fields.Float(
        compute='_average_consumption',
        string='Number of days for the calculation',
        help="""The calculation will be done for the last 365 days or"""
        """ since the first purchase or sale of the product if it's"""
        """ more recent""")

    @api.multi
    def _min_date(self):
        self.ensure_one()
        query = """SELECT to_char(min(date), 'YYYY-MM-DD') \
                from stock_move
                where product_id = %s
                GROUP BY product_id""" % (self.id)
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        return results and results[0] and results[0][0] \
            or time.strftime('%Y-%m-%d')

    @api.multi
    def _average_consumption(self):
        self.refresh()
        product_ids = [p.id for p in self]
        self.calculate_average_days(product_ids, 365)
        self.calculate_average_days(product_ids, 15)
        self.calculate_average_days(product_ids, 30)
        self.calculate_average_days(product_ids, 90)
        return True

    @api.multi
    def calculate_average_days(self, product_ids, n_days):
        first_date = time.strftime('%Y-%m-%d')
        domain_move_out, begin_date, ctx = self.get_domain(product_ids, n_days)
        moves_out = self.env['stock.move'].read_group(
            domain_move_out, ['product_id', 'product_qty'], ['product_id'])
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']),
                             moves_out))
        for product in self:
            qty_out = float_round(
                moves_out.get(product.id, 0.0),
                precision_rounding=product.uom_id.rounding)
            first_date = max(begin_date, product.with_context(ctx)._min_date())
            if n_days == 365:
                nb_days = (
                    datetime.datetime.today() -
                    datetime.datetime.strptime(first_date, '%Y-%m-%d')
                ).days or 1.0
                product.average_consumption = (
                    nb_days and qty_out / nb_days or 0.0)
                product.total_consumption = qty_out or 0.0
                if product.total_consumption == 0:
                    product.nb_days = 0.0
                else:
                    product.nb_days = nb_days or 0.0
            elif n_days == 15:
                product.average_consumption_15 = qty_out / 15 or 0.0
                product.total_consumption_15 = qty_out or 0.0
            elif n_days == 30:
                product.average_consumption_30 = qty_out / 30 or 0.0
                product.total_consumption_30 = qty_out or 0.0
            elif n_days == 90:
                product.average_consumption_90 = qty_out / 90 or 0.0
                product.total_consumption_90 = qty_out or 0.0

    @api.multi
    def get_domain(self, product_ids, n_days):
        begin_date = (
            datetime.datetime.today() -
            datetime.timedelta(days=n_days)).strftime('%Y-%m-%d')
        ctx = dict(self.env.context)
        ctx.update({
            'from_date': begin_date
        })
        domain_products = [('product_id', 'in', product_ids)]
        domain_move_out = []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
            self._get_domain_locations()
        domain_move_out += self._get_domain_dates(ctx) \
            + [('state', 'in', ('confirmed', 'waiting', 'assigned', 'done'))] \
            + domain_products
        domain_move_out += domain_move_out_loc
        return domain_move_out, begin_date, ctx

    def _get_domain_dates(self, context):
        from_date = context.get('from_date', False)
        to_date = context.get('to_date', False)
        domain = []
        if from_date:
            domain.append(('date', '>=', from_date))
        if to_date:
            domain.append(('date', '<=', to_date))
        return domain
