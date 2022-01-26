from colorspace.colorlib import HCL
from colormath.color_objects import LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cmc
import numpy as np
import random

class HPaletteGenerator():
    def __init__(self,n=1000,hrange=[20,360],crange=[30,80],lrange=[35,80]):
        self.total_colors=n
        self.hrange = hrange
        self.crange = crange
        self lrange = lrange

    def genpal(self):

        palette = []
        palette_class = []
        # Divide hrange by 1000
        hvalues = np.arange(start=20,stop=360,step=1)
        hvalue_dict = {}
        for itm in hvalues:
            hvalue_dict[itm] = itm

        cvalues = np.arange(start=30,stop=80,step=1)
        cvalue_dict = {}
        for itm in cvalues:
            cvalue_dict[itm] = itm

        lvalues = np.arange(start=30,stop=80,step=1)
        lvalue_dict = {}
        for itm in lvalues:
            lvalue_dict[itm] = itm

        # This could take a long time
        while len(palette)<self.total_colors:
            # Pick random across field
            hrand = random.randint(self.hrange[0],self.hrange[1])
            crand = random.randint(self.crange[0],self.crange[1])
            lrand = random.randint(self.lrange[0],self.lrange[1]) 

            # Make temp color
            color = (hrand,crand,lrand)
            if len(palette)=0:
                newc = HCL(H=hrand,C=crand,L=lrand)
                palette.append(color)
                palette_class.append(newc)
            else:
                if color not in palette:
                    newc = HCL(H=hrand,C=crand,L=lrand)

                    for itm in palette_class:
                        









        return palette
