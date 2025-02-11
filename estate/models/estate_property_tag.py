from odoo import fields, models

class EstatePropertyTag(models.Model):
    _name="estate.property.tag"
    _description="Property Tags"
    _order = "name"

    name = fields.Char("Name",required=True)
    color = fields.Integer("Color", default=1)

    _sql_constraints = [
        ('unique_property_tag', 'unique(name)', 'Tag name must be unique')
    ]