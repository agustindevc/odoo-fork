from odoo import models, Command

class EstateProperty(models.Model):
    _inherit = 'estate.property'

    def action_mark_sold(self):
        res = super().action_mark_sold()
        for property in self:
            property = self.browse(property.id)  
            print('DEBUG selling_price:', property.selling_price)
            if property.buyer_id:
                journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                commission = property.selling_price * 0.06
                self.env.cr.commit() 
                self.env['account.move'].create({
                    'partner_id': property.buyer_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'invoice_line_ids': [
                        Command.create({
                            'name': 'Comisión inmobiliaria',
                            'quantity': 1,
                            'price_unit': commission,
                        }),
                        Command.create({
                            'name': 'Gastos administrativos',
                            'quantity': 1,
                            'price_unit': 100.0,
                        }),
                    ],
                })
        return res
