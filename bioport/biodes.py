##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
# 
# This file is part of bioport.
# 
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

import grok
from bioport.app import Bioport
from bioport.app import RepositoryView

import zope.interface

class BioDes(grok.Container):
    grok.template('index')
    def repository(self):
        return self.__parent__.repository()
    
class Beschrijving(grok.View, RepositoryView):
    pass

class Index(grok.View, RepositoryView):
    pass

class Persoonsnaam(grok.View, RepositoryView):
    pass

class Schemas(grok.View, RepositoryView):
    pass

class Voorbeelden(grok.View, RepositoryView):
    pass
class Partners(grok.View, RepositoryView):
    pass