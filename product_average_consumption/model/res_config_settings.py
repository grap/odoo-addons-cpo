# © 2021 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_average_consumption_states = fields.Char(
        'Product Average Consumption Move States',
        help='Comma separated list of move states used to compute the average'
        ' consumption of products',
        related='company_id.product_average_consumption_states'
    )
    product_average_consumption_location_ids = fields.Many2many(
        'stock.location',
        related='company_id.product_average_consumption_location_ids',
        string="Product Average Consumption: Destination Locations"
    )
    @api.model
    def _get_product_average_consumption_order_dates(self):
        product_average_consumption_order_dates = self.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', 'in', [
                'create_date', 'write_date'])
        ])
        return [
            (field.name, field.field_description)
            for field in sorted(product_average_consumption_order_dates, key=lambda f: f.field_description)
        ]

    product_average_consumption_order_dates = fields.Selection(
        _get_product_average_consumption_order_dates,
        string='Product Average Consumption: Order dates',
        default='create_date'
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        ir_config_sudo = self.env['ir.config_parameter'].sudo()
        order_days = ir_config_sudo.get_param(
            'product_average_consumption_order_dates')
        res.update(
            product_average_consumption_order_dates=(
                order_days),
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'product_average_consumption_order_dates', self.product_average_consumption_order_dates)