# © 2021 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    product_average_consumption_states = fields.Char(
        "Product Average Consumption Move States"
    )
    product_average_consumption_location_ids = fields.Many2many(
        "stock.location",
        relation="res_company_avg_consumption_location_rel",
        column1="company_id",
        column2="location_id",
        string="Product Average Consumption: Destination Locations",
    )
