''' BIR to Bluespec translation
'''
import os
import yaml
import logging
import argparse

from pif_ir.meta_ir.instance import MetaIRInstance

from pif_ir.bir.objects.metadata_instance import MetadataInstance
from pif_ir.bir.objects.packet_instance import PacketInstance
from pif_ir.bir.objects.processor import Processor
from pif_ir.bir.objects.table_entry import TableEntry

from pif_ir.bir.utils.exceptions import BIRError
from pif_ir.bir.utils.bir_parser import BIRParser

from bsvgen_control_flow import BSVControlFlow
from bsvgen_basic_block import BSVBasicBlock
from bsvgen_bir_struct import BSVBIRStruct
from bsvgen_table import BSVTable
from programSerializer import ProgramSerializer

class BirInstance(MetaIRInstance):
    ''' TODO '''
    def __init__(self, name, inputfile):
        """
        @brief BirInstance constructor

        @param name The name of the instance
        @param input An object with the YAML description of the BIR instance
        @param transmit_handler A function to be called to transmit pkts
        """
        local_dir = os.path.dirname(os.path.abspath(__file__))
        bir_meta_yml = os.path.join(local_dir, 'bir_meta.yml')
        super(BirInstance, self).__init__(bir_meta_yml)

        self.name = name
        self.add_content(inputfile)

        # create parsers to handle next_control_states, and the
        # F instructions
        bir_parser = BIRParser()

        # BIR objects
        self.bir_structs = {}
        self.bir_tables = {}
        self.bir_other_modules = {}
        self.bir_basic_blocks = {}
        self.bir_control_flows = {}
        self.bir_other_processors = {}
        self.start_processor = []
        self.table_init = []

        for name, val in self.struct.items():
            self.bir_structs[name] = BSVBIRStruct(name, val)
        for name, val in self.table.items():
            self.bir_tables[name] = BSVTable(name, val)
        for name, val in self.other_module.items():
            for operation in val['operations']:
                module = "{}.{}".format(name, operation)
                self.bir_other_modules[module] = self._load_module(name, operation)
        for name, val in self.basic_block.items():
            self.bir_basic_blocks[name] = BSVBasicBlock(name, val,
                                                        self.bir_structs,
                                                        self.bir_tables,
                                                        self.bir_other_modules,
                                                        bir_parser)
        for name, val in self.control_flow.items():
            self.bir_control_flows[name] = BSVControlFlow(name, val,
                                                          self.bir_basic_blocks,
                                                          self.bir_structs,
                                                          bir_parser)
        for name, val in self.other_processor.items():
            self.bir_other_processors[name] = self._load_processor(name,
                                                                   val['class'])

        # BIR processor layout
        for layout in self.processor_layout.values():
            if layout['format'] != 'list':
                logging.error("usupported layout format")
                exit(1)

            last_proc = None
            for proc_name in layout['implementation']:
                curr_proc = self._get_processor(proc_name)
                if last_proc == None:
                    self.start_processor = curr_proc
                else:
                    last_proc.next_processor = curr_proc
                last_proc = curr_proc
            #last_proc.next_processor = self.transmit_processor

    def _get_processor(self, name):
        ''' TODO '''
        if name in self.bir_control_flows.keys():
            return self.bir_control_flows[name]
        elif name in self.bir_other_processors.keys():
            return self.bir_other_processors[name]
        else:
            raise BIRError("unknown processor: {}".format(name))

    def generatebsv(self, serializer):
        ''' TODO '''
        for item in self.bir_structs.values():
            item.bsvgen(serializer)
        for item in self.bir_tables.values():
            item.bsvgen(serializer)
        for item in self.bir_control_flows.values():
            item.bsvgen(serializer)

def main():
    ''' entry point '''
    argparser = argparse.ArgumentParser(
        description="BIR to Bluespec Translator")
    argparser.add_argument('-y', '--yaml', required=True,
                           help='Input BIR YAML file')
    argparser.add_argument('-o', '--output', required=True,
                           help='Output BSV file')
    options = argparser.parse_args()

    bir = BirInstance('p4fpga', options.yaml)
    serializer = ProgramSerializer()
    bir.generatebsv(serializer)

    if not os.path.exists(os.path.dirname(options.output)):
        os.makedirs(os.path.dirname(options.output))
    with open(options.output, 'w') as bsv:
        bsv.write(serializer.toString())

if __name__ == "__main__":
    main()
