# © 2021 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
from odoo import fields, models


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
