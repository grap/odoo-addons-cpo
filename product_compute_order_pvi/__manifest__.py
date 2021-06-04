# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
{
    'name': 'Product - Average Consumption PVI',
    'version': '11.0.1.0.0',
    'category': 'Purchase',
    'author': 'FactorLibre',
    'license': 'AGPL-3',
    'depends': [
        'purchase_compute_order',
        'product_compute_order_pvi',
        'sale',
    ],
    'data': [
        'views/product_view.xml',
        'views/computed_purchase_order.xml'
    ],
    'installable': True,
}
