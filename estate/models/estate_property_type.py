from odoo import models, fields

# Modelo para tipos de propiedad en la app estate
class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'
    _order = "sequence, name"
    


    # Nombre del tipo de propiedad
    name = fields.Char(string='Name', required=True)

    # Secuencia para ordenar los tipos de propiedad
    sequence = fields.Integer(string="Sequence")

    # Propiedades asociadas a un tipo
    property_ids = fields.One2many(
        "estate.property",
        "property_type_id",
        string="Properties"
    )

    # Ofertas asociadas a un tipo de propiedad
    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_type_id',
        string='Offers'
    )

    # Cantidad de ofertas para un tipo de propiedad
    offer_count = fields.Integer(
        string='Offer Count',
        compute='_compute_offer_count'
    )


    def _compute_offer_count(self):
        # Calcula la cantidad de ofertas asociadas a este tipo
        for rec in self:
            rec.offer_count = len(rec.offer_ids)


    # Asegura que el nombre del tipo de propiedad sea único
    _sql_constraints = [
        ('unique_type_name',
         'UNIQUE(name)',
         'El nombre del tipo de propiedad debe ser único.')
    ]