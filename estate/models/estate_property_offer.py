from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.odoo.exceptions import UserError, ValidationError


class EstatePropertyOffer(models.Model):
    _name="estate.property.offer"
    _description="Real Estate Property Offer"
    _order = "price desc"

    price = fields.Float("Price", required=True)
    status = fields.Selection([("accepted", "Accepted"), ("refused", "Refused")], string="Status", copy=False)
    partner_id = fields.Many2one("res.partner", required=True, string="Partner")
    property_id = fields.Many2one("estate.property", required=True, string="Property")
    validity = fields.Integer("Validity (Days)", default=7)
    date_deadline = fields.Date("Deadline", compute="_compute_deadline", inverse="_inverse_deadline")
    property_type_id = fields.Many2one("estate.property.type", related="property_id.property_type_id", string="Property Type", store=True)

    _sql_constraints = [
        ('check_offer_price', 'CHECK(price > 0)',
         'The offer price must be positive')
    ]

    @api.depends("create_date", "validity")
    def _compute_deadline(self):
        for offer in self:
            if offer.create_date:
                offer.date_deadline = offer.create_date + timedelta(days=offer.validity)
            else:
                offer.date_deadline = fields.Date.today() + timedelta(days=offer.validity)

    def _inverse_deadline(self):
        for offer in self:
            if offer.create_date and offer.date_deadline:
                offer.validity = (offer.date_deadline - offer.create_date.date()).days
            elif offer.date_deadline:
                offer.validity = (offer.date_deadline - fields.Date.today()).days

    def action_accept_offer(self):
        for offer in self:
            if offer.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != offer.id):
                raise UserError('You can only accept one offer per property')
            offer.status = "accepted"
            offer.property_id.state = "accepted"
            offer.property_id.selling_price = offer.price
            offer.property_id.buyer = offer.partner_id
        return True


    def action_reject_offer(self):
        for offer in self:
            if offer.status == "refused":
                raise UserError('Offer already rejected')
            offer.status = "refused"
        return True


    @api.model
    def create(self, vals):
        offer_property = self.env["estate.property"].browse(vals["property_id"])

        if offer_property.offer_ids.filtered(lambda o: o.price > vals["price"]):
            raise ValidationError("Offer price must be higher than existing offers.")

        offer_property.state = "received"

        return super().create(vals)