from odoo import fields, models

# Modelo para etiquetas de propiedades
class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Property Tag"
    _order = "name"
    _rec_name = "name"

    # Nombre de la etiqueta
    name = fields.Char(required=True)
    color = fields.Integer()

    # Asegura que no se repitan nombres de etiquetas
    _sql_constraints = [
        ('unique_tag_name',
         'UNIQUE(name)',
         'The tag name must be unique.')
    ]
