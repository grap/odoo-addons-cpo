# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, api, fields
import datetime
import time


class ProductProduct(models.Model):
    _inherit = 'product.product'

    average_consumption_pvi = fields.Float("Average Consumption with PVI",
                                           compute='_average_consumption_pvi')

    @api.multi
    def _average_consumption_pvi(self):
        parametres = ['draft', 'pvi_confirmed', 'sent']
        self.calculate_average_consumption_pvi(parametres)

    @api.multi
    def calculate_average_consumption_pvi(self, parametres):
        for product in self:
            begin_date = (datetime.datetime.today() -
                          datetime.timedelta(days=365)).strftime('%Y-%m-%d')
            date = max(begin_date, product._min_date_draft())
            sale_ids = self.env['sale.order'].search([
                ('date_order', '>=', date)
            ]).ids
            line_ids = self.env['sale.order.line'].search([
                ('state', 'in', parametres),
                ('order_id', 'in', sale_ids),
                ('product_id', '=', product.id)
            ])
            consumption = 0
            nb_days = (datetime.datetime.today() -
                       datetime.datetime.strptime(
                       min(product._min_date(), date), '%Y-%m-%d')).days or 1.0
            for line in line_ids:
                consumption += line.product_uom_qty
            product.average_consumption_pvi =\
                (consumption + product.total_consumption) / nb_days

    @api.multi
    def custom_average_consumption(self, parametres, pvi):
        self.ensure_one()
        begin_date = (datetime.datetime.today() -
                      datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        date = max(begin_date, self._min_date_draft())
        sale_ids = []
        if True in pvi:
            sale_ids += self.env['sale.order'].search([
                ('date_order', '>=', date),
                ('initial_order', '=', True)
            ]).ids
        if False in pvi:
            sale_ids += self.env['sale.order'].search([
                ('date_order', '>=', date),
                ('initial_order', '=', False)
            ]).ids
        line_ids = self.env['sale.order.line'].search([
            ('state', 'in', parametres),
            ('order_id', 'in', sale_ids),
            ('product_id', '=', self.id)
        ])
        consumption = 0
        nb_days = (datetime.datetime.today() -
                   datetime.datetime.strptime(
                   min(self._min_date(), date), '%Y-%m-%d')).days or 1.0
        for line in line_ids:
            if line.state == 'pvi_confirmed':
                consumption += line.uom_remaining_qty
            else:
                consumption += line.product_uom_qty
        return [consumption, (consumption / nb_days)]

    @api.multi
    def _min_date_draft(self):
        self.ensure_one()
        query = """SELECT to_char(min(so.date_order), 'YYYY-MM-DD') \
                from sale_order as so
                inner join sale_order_line as sol
                    on so.id = sol.order_id
                where sol.product_id = %s""" % (self.id)
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        return results and results[0] and results[0][0] \
            or time.strftime('%Y-%m-%d')

    @api.multi
    def _get_draft_outgoing_qty(self):
        super(ProductProduct, self)._get_draft_outgoing_qty()
        sol_obj = self.env['sale.order.line']
        sale_ids = self.env['sale.order'].search([
            ('initial_order', '=', False)
        ]).ids
        sol_ids = sol_obj.search([
            ('state', '=', 'draft'),
            ('order_id', 'in', sale_ids),
            ('product_id', 'in', [p.id for p in self])
        ])
        draft_qty = {}
        for line in sol_ids:
            draft_qty.setdefault(line.product_id.id, 0)
            draft_qty[line.product_id.id] += \
                line.product_uom_qty / line.product_uom.factor\
                * line.product_id.uom_id.factor
        for pp in self:
            pp.draft_outgoing_qty += draft_qty.get(pp.id, 0)
