# -*- encoding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2009 Domsense SRL (<http://www.domsense.com>). 
#    All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Gestione Riparazioni In Garanzia e Non',
    'version': '0.1',
    'category': 'purchase mrp',
    'description': """ Gestione delle richieste di riparazione in garanzia e non 
    
     """,
    'author': 'C & G Software sas',
    'website': 'http://www.cgsoftware.it',
    "depends" : ['product','stock','base','mrp_repair'],
    "update_xml" : [
                    'mrp_repair_view.xml',
                    
                    ],
    "active": False,
    "installable": True
}

