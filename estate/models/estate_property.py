from datetime import timedelta
from odoo import api, fields, models
from odoo.odoo.exceptions import UserError, ValidationError
from odoo.odoo.tools import float_is_zero, float_compare


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"

    name = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(string="Available From",copy=False, default=lambda self: fields.Date.today() + timedelta(days=90))
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price",readonly=True, copy=False)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer(string="Number of Facades")
    garage = fields.Boolean(string="Has Garage?")
    garden = fields.Boolean(string="Has Garden?")
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection([
        ("north", "North"),
        ("south", "South"),
        ("east", "East"),
        ("west", "West")
    ], string="Garden Orientation"
    )
    active = fields.Boolean(required=True, default=False)
    state = fields.Selection([
        ("new", "New"),
        ("received", "Offer Received"),
        ("accepted", "Offer Accepted"),
        ("sold", "Sold"),
        ("cancelled", "Cancelled")
    ], required=True, copy=False, default="new", string="Status")
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    buyer = fields.Many2one("res.partner", copy=False, string="Buyer")
    salesperson = fields.Many2one("res.users", string="Sales Person", default=lambda self: self.env.user.id)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Integer('Total Area (sqm)', compute="_compute_total_area")
    best_price = fields.Float('Best Offer', compute="_compute_best_offer")

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)',
         'The expected price must be positive'),
        ('check_selling_price', 'CHECK(selling_price > 0)',
         'The selling price must be positive')
    ]


    @api.constrains("expected_price", "selling_price")
    def _check_selling_price(self):
        for record in self:
            if not float_is_zero(record.selling_price, precision_rounding=0.01):
                min_price = record.expected_price * 0.9
                if float_compare(min_price, record.expected_price, precision_rounding=0.01) < 0:
                    raise ValidationError(f"""
                    The selling price must be at least 90% of the expected price. 
                    You must reduce the expected price if you want to accept this offer.
                    """)



    @api.depends("garden_area", "living_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area


    @api.depends("offer_ids.price")
    def _compute_best_offer(self):
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped("price"))
            else:
                record.best_price = 0.00


    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10.0
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = None


    def action_mark_sold(self):
        for record in self:
            if record.state == "cancelled":
                raise UserError("Property cancelled cannot be sold")
            else:
                record.state = "sold"
        return True


    def action_mark_cancelled(self):
        for record in self:
            if record.state == "sold":
                raise UserError("Property sold cannot be cancelled")
            else:
                record.state = "cancelled"
        return True


    @api.ondelete(at_uninstall=False)
    def _unlink_if_new_or_cancelled(self):
        for record in self:
            if record.state != "cancelled" or record.state != "new":
                raise UserError("Cannot delete property")
