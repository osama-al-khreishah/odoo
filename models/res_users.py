from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    property_type_ids = fields.One2many(
        comodel_name='estate.property',  
        inverse_name='salesperson_id',   
        string='Properties'              
    )
