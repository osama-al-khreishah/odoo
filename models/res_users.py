
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many(
        comodel_name='estate.property',  # The related model
        inverse_name='salesperson_id',   # The inverse Many2one field in estate.property
        string='Properties'              # Label for the field
    )
                                