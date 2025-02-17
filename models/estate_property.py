from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

# -----------------------------Estate propert type model------------------------------------------
class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Real Estate Property Type"
    _order = "sequence"


    name = fields.Char(string="Type", required=True)
    sequence = fields.Integer(string="Sequence", default=10)

# ------------------------------Estate property tag model-----------------------------------------
class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Real Estate Property Tag"

    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color Index")

# -----------------------------Estate property ofer model-----------------------------------------
class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"
    _order = "price desc"

    price = fields.Float(string="Price", required=True)
    status = fields.Selection(
        string="Status",
        selection=[("accepted", "Accepted"), ("refused", "Refused")],
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_type_id = fields.Many2one("estate.property", string="Property", required=True)
    offer_ids = fields.One2many("estate.property.offer", "property_type_id", string="Offers")
    offer_count=fields.Integer(compute="_compute_offer_count", string="Offer Count")
    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(string="Deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline")

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + relativedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                record.validity = (record.date_deadline - record.create_date.date()).days

    

# ----------------------------Main estate property model----------------------------------------

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "sequence"

    # **************Defintion of fields************
    
    name = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(string="Available From", copy=False)
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price", readonly=True, copy=False)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer(string="Facades")
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
    garden_area = fields.Integer(string="Garden Area (sqm)")
    
    #*****************Selection feilds********************
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")],
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        string="Status",
        selection=[("new", "New"), ("offer_received", "Offer Received"), ("offer_accepted", "Offer Accepted"),
                   ("sold", "Sold"), ("canceled", "Canceled")],
        default="new",
        required=True,
        copy=False,
    )

    # ***************Security relations definitions*******************
    
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    salesperson_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_type_id", string="Offers")

    # ********************Fields with calculations*********************
    
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area (sqm)", store=True)
    best_price = fields.Float(compute="_compute_best_price", string="Best Offer", store=True)

    # ************************Sequence field*****************************
    
    sequence = fields.Integer(string="Sequence", default=1, help="Used to order properties. Lower is better.")

    # ********************SQL Constraints (Checks for the input)**************************
    
    _sql_constraints = [
        (
            'check_expected_price',  # Constraint name
            'CHECK(expected_price > 0)',  # SQL condition
            "The expected price must be positive."  # Error message
        ),
        (
            'check_selling_price',  # Constraint name
            'CHECK(selling_price >= 0)',  # SQL condition
            "The selling price cannot be negative."  # Error message
        ),
    ]
    #********************************Action methods****************************************
    def action_sold(self):

        for record in self:
            if record.state == "canceled":
                raise UserError("Canceled properties cannot be marked as sold.")
            if not record.offer_ids.filtered(lambda offer: offer.status == "accepted"):
                raise UserError("A property can only be sold if there is an accepted offer.")
            record.state = "sold"
            

    def action_cancel(self):
    
        for record in self:
            if record.state == "sold":
                raise UserError("Sold properties cannot be canceled.")
            property.state = "canceled"

    def unlink(self):
                     
        for record in self:
            if record.state not in ['new', 'canceled']:
                raise UserError("You can only delete properties that are in 'New' or 'Canceled' state.")  
        return super(EstateProperty, self).unlink()
    
    # *********************Calculations for calculated fields********************
   
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped("price")) if record.offer_ids else 0.0
    
    # **********************Action methods for the buttons**************************
    
    @api.ondelete(at_uninstall=False)
    def _unlink_if_state_new_or_canceled(self):
        for record in self:
            if record.state not in ["new", "canceled"]:
                raise UserError("You can only delete properties that are in 'New' or 'Canceled' state.")
            
    @api.model
    def create(self, vals):
        property_id = vals.get('property_id')
        if property_id:
            property = self.env['estate.property'].browse(vals["property_id"])

            # Check if the new offer has a lower price than existing offers
            existing_offers = property.offer_ids
            for offer in existing_offers:
                if vals['price'] < offer.price:
                    raise UserError("You cannot create an offer with a lower amount than an existing offer.")
            property.state = 'offer_received'

        return super(EstatePropertyOffer, self).create(vals)