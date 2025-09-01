from odoo import models, fields

# Extiende el modelo de usuarios para agregar relación con propiedades
class ResUsers(models.Model):
    _inherit = "res.users"

    # Propiedades a la venta asociadas a este usuario (solo nuevas o con oferta recibida)
    property_ids = fields.One2many(
        "estate.property",
        "seller_id",
        string="Propiedades a la venta",
        domain=[("state", "in", ["new", "offer_received"])]
    )
