# -*- coding: utf-8 -*-

from osv import fields,osv
import netsvc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _
import decimal_precision as dp



class mrp_repair(osv.osv):
    _inherit = 'mrp.repair' 
    #Do not touch _name it must be same as _inherit
    #_name = 'mrp.repair' cr = 'mrp.repair'
    
    def _costo_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for repair in self.browse(cr, uid, ids, context=context):
            res[repair.id] = 0.0
            for line in repair.operations:
                res[repair.id] += line.costo_subtotal
            cur = repair.pricelist_id.currency_id
            res[repair.id] = cur_obj.round(cr, uid, cur, res[repair.id])
        print 'Costo Totale',res
        return res
        
    
    _columns = {
                 'origin':fields.char('Origine', size=64, required=False, readonly=False),
                 'operations' : fields.one2many('mrp.repair.line', 'repair_id', 'Operation Lines', readonly=False, states={'done':[('readonly',True)]}),
                 'production_id': fields.many2one('mrp.production', 'Id. Produzione'),
                 'costo_total': fields.function(_costo_total, method=True, string='Total'),                 
                 'costo_medio_prima':fields.float('Costo Unitario', required=False, digits_compute= dp.get_precision('Account')),    
                 
                    }


    def action_repair_done(self, cr, uid, ids, context=None):
        res = super(mrp_repair, self).action_repair_done(cr, uid, ids, context=context)
        # aggioerna il costo medio dell'articolo in riparazione avendo poi anche la produzione di appartenenza 
        # è facile anche fare una statistica del costo di produzione singola calcolato
        for repair in self.browse(cr, uid, ids, context=context):
            if repair.product_id.cost_method == 'average':
                riga_rep = {
                        'costo_medio_prima':repair.product_id.standard_price,
                        
                        }
                #import pdb;pdb.set_trace()
                new_c_medio = ((repair.product_id.standard_price* repair.product_id.qty_available)+repair.costo_total)/repair.product_id.qty_available
                print 'Standard ',repair.product_id.standard_price
                print 'Qty ',repair.product_id.qty_available
                print 'Costo ',repair.costo_total
                print "((repair.product_id.standard_price* repair.product_id.qty_available)+repair.costo_total)/repair.product_id.qty_available  = ",new_c_medio
                riga_prod ={
                            'standard_price':new_c_medio,
                            }
                ok = self.pool.get('product.product').write(cr,uid,[repair.product_id.id],riga_prod)
                ok = self.pool.get('mrp.repair').write(cr,uid,[repair.id],riga_rep)
        return res

mrp_repair()



class ProductChangeMixin(object):
    def product_id_change(self, cr, uid, ids, pricelist, product, uom=False,
                          product_uom_qty=0, partner_id=False, guarantee_limit=False,parent_product=False):
        """ On change of product it sets product quantity, tax account, name,
        uom of product, unit price and price subtotal.
        @param pricelist: Pricelist of current record.
        @param product: Changed id of product.
        @param uom: UoM of current record.
        @param product_uom_qty: Quantity of current record.
        @param partner_id: Partner of current record.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values and warning message.
        """
        result = {}
        warning = {}
        #import pdb;pdb.set_trace()
        if not product_uom_qty:
            product_uom_qty = 1
        result['product_uom_qty'] = product_uom_qty

        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            if partner_id:
                partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
                result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, product_obj.taxes_id)
            result['name'] = product_obj.partner_ref
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id or False
            result['costo_unit'] = product_obj.standard_price
            if not pricelist:
                warning = {
                    'title':'No Pricelist !',
                    'message':
                        'You have to select a pricelist in the Repair form !\n'
                        'Please set one before choosing a product.'
                }
            else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                            product, product_uom_qty, partner_id, {'uom': uom,})[pricelist]

                if price is False:
                     warning = {
                        'title':'No valid pricelist line found !',
                        'message':
                            "Couldn't find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist."
                     }
                else:
                    result.update({'price_unit': price, 'price_subtotal': price*product_uom_qty})
            if parent_product:
                #import pdb;pdb.set_trace()
                cerca=[('product_id','=',parent_product)]
                id_bom = self.pool.get('mrp.bom').search(cr,uid,cerca)
                if id_bom:
                    bom = self.pool.get('mrp.bom').browse(cr,uid,id_bom)[0]
                    cerca=[('bom_id','=',id_bom[0]),('product_id','=',product)]
                    id_line_bom = self.pool.get('mrp.bom.altern.comp').search(cr,uid,cerca)
                    if id_line_bom:
                        line_bom= self.pool.get('mrp.bom.altern.comp').browse(cr,uid,id_line_bom)[0]
                        if line_bom:
                            
                            result.update({'product_uom_qty':line_bom.product_qty,'price_unit': price, 'price_subtotal': price*line_bom.product_qty,})
                        else:
                            line_bom= self.pool.get('mrp.bom.facoltativi.comp').browse(cr,uid,id_line_bom)[0]
                            if line_bom:
                                result.update({'product_uom_qty':line_bom.product_qty,'price_unit': price, 'price_subtotal': price*line_bom.product_qty,})                            
        return {'value': result, 'warning': warning}


class mrp_repair_line(osv.osv, ProductChangeMixin):
    _inherit = 'mrp.repair.line'
    
    def _cost_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj=self.pool.get('res.currency')
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            cur = line.repair_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, line.costo_unit*line.product_uom_qty)
        print "RES ", res
        return res
    
    _columns ={
               'costo_unit': fields.float('Costo Unitario', required=True, digits_compute= dp.get_precision('Account')),
               'costo_subtotal': fields.function(_cost_line, method=True, string='Costo Totale Riga',digits_compute= dp.get_precision('Account')),
               }

    _defaults = {
     'state': lambda *a: 'draft',
     'product_uom_qty': 0,
     'type':'add',
     'to_invoice': False,
    }


    def default_get(self, cr, uid, fields, context=None):
        #import pdb;pdb.set_trace()
        data = super(mrp_repair_line, self).default_get(cr, uid, fields, context=context)
        location_id = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock Lequile')])[0]
        location_dest_id = self.pool.get('stock.location').search(cr, uid, [('name','=','Production')])[0]
        data['location_id']=location_id
        data['location_dest_id']=location_dest_id
        return data

    def onchange_operation_type(self, cr, uid, ids, type, guarantee_limit):
        
        #res = super(mrp_repair_line,self).onchange_operation_type(cr, uid, ids, type, guarantee_limit)
        
        #value={}
        
        #value = res.get('value')
        
        #import pdb;pdb.set_trace()
        
        location_id = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock Lequile')])[0]
        location_dest_id = self.pool.get('stock.location').search(cr, uid, [('name','=','Production')])[0]
        
        if not type:
            return {'value': {
                'location_id': False,
                'location_dest_id': False
                }
            }
        
        if type == 'add':
            #SI E' SCELTO DI AGGIUNGERE (SOSTITUIRE UN COMPONENTE), VERRA' PRELEVATO DAL MAGAZZINO CENTREALE (STOCK LEQUILE)
            # E CARICATO NEL MAGAZZINO (produzione)
            return {'value': {
                'to_invoice': False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                }
            }
            #IN CASO DI SOLA RIMOZIONE DEL COMPONENTE DANNEGGIATO LO PRELEVO E LO RICARICO DA GARANZIA SEDE
        else:
            return {'value': {
                'to_invoice': False,
                'location_id': location_dest_id,
                'location_dest_id': location_dest_id,                }
                    
            }
            
        

mrp_repair_line()