'''
Struct with bsv backend
'''

from pif_ir.bir.objects.bir_struct import BIRStruct
from sourceCodeBuilder import SourceCodeBuilder
from bsvgen_common import generate_typedef
from dotmap import DotMap

def CamelCase(name):
    ''' CamelCase '''
    output = ''.join(x for x in name.title() if x.isalnum())
    return output

class BSVBIRStruct(BIRStruct):
    '''
    TODO
    '''
    def __init__(self, name, struct_attrs):
        super(BSVBIRStruct, self).__init__(name, struct_attrs)

    def serialize(self):
        ''' Serialize struct to JSON '''
        json = DotMap()
        for k, v in self.fields.items():
            json.field[k] = v
        return json

    def bsvgen(self, builder):
        ''' TODO '''
        assert isinstance(builder, SourceCodeBuilder)
        out = generate_typedef(self)
        builder.append(out)

