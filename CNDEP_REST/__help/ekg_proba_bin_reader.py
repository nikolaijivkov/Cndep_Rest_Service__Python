import binascii
import time
import inspect
import os
import svgwrite
import random
path=os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))+os.sep

def create_svg(name='test', array={}, scale=1.0/125, time_scale=4):
    max=0
    for i in range(0,len(array)):
        if(max < abs(array[i])*scale):
            max = abs(array[i])*scale
    
    svg_size = max+max*scale
    font_size = 20
    
    title = name
    
    dwg = svgwrite.Drawing('svg\\'+name+'.svg', (svg_size*10, svg_size*2), debug=True)
    # background will be white.
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='white'))
    # give the name of the example and a title.
    text = dwg.add(dwg.g(font_family="sans-serif", font_size=font_size, fill='black'))
    lines = dwg.add(dwg.g(stroke_width=1.5, stroke='green', fill='none'))

    text.add(dwg.text(title, insert=(0, (font_size + 5))))
    
    back_off=svg_size
    end_point=(1*time_scale, back_off-int(array[i]*scale))
    for i in range(1,len(array)): #
        start_point=end_point
        #print start_point
        end_point=((i+1)*time_scale, back_off-int(array[i]*scale)) #random.randint(0,back_off)
        #print end_point
        lines.add(dwg.line(start=start_point, end=end_point))
        #time.sleep(4)
    dwg.save()

def main():
    fd=open(path+"ekg_proba.bin")
    read_size=16
    fd.read(16) #skip first 16 bytes metadata

    I={}
    II={}
    III={}
    avR={}
    avL={}
    avF={}
    V1={}
    V2={}
    V3={}
    V4={}
    V5={}
    V6={}

    Ij={}
    IIj={}
    IIIj={}
    avRj={}
    avLj={}
    avFj={}
    V1j={}
    V2j={}
    V3j={}
    V4j={}
    V5j={}
    V6j={}
    
    run_flag=1
    k=0
    i=0
    while run_flag:
        for j in range(0,4):
            data = fd.read(read_size)
            if(not data or len(data)!=16):
                if(k<4):
                    k+=1
                    fd.close()
                    time.sleep(0.5)
                    fd=open(path+"ekg_proba.bin")
                    fd.read(16) #skip first 16 bytes metadata
                    data = fd.read(read_size)
                else:
                    fd.close()
                    run_flag=0
                    break
            Ch0=float(int(data[0:2].encode('hex'),16))
            Ch1=float(int(data[2:4].encode('hex'),16))
            Ch2=float(int(data[4:6].encode('hex'),16))
            Ch3=float(int(data[6:8].encode('hex'),16))
            Ch4=float(int(data[8:10].encode('hex'),16))
            Ch5=float(int(data[10:12].encode('hex'),16))
            Ch6=float(int(data[12:14].encode('hex'),16))
            Ch7=float(int(data[14:16].encode('hex'),16))
        
            Ij[j]=Ch4-Ch0
            IIj[j]=-Ch0
            IIIj[j]=-Ch4
            avRj[j]=(Ch0-Ch4)/2
            avLj[j]=(Ch4-Ch0)/2
            avFj[j]=-(Ch0+Ch4)/2
            V1j[j]=Ch1-(Ch0+Ch4)/3
            V2j[j]=Ch5-(Ch0+Ch4)/3
            V3j[j]=Ch2-(Ch0+Ch4)/3
            V4j[j]=Ch6-(Ch0+Ch4)/3
            V5j[j]=Ch3-(Ch0+Ch4)/3
            V6j[j]=Ch7-(Ch0+Ch4)/3
            
        I[i]=(Ij[0]+Ij[1]+Ij[2]+Ij[3])/4
        II[i]=(IIj[0]+IIj[1]+IIj[2]+IIj[3])/4
        III[i]=(IIIj[0]+IIIj[1]+IIIj[2]+IIIj[3])/4
        avR[i]=(avRj[0]+avRj[1]+avRj[2]+avRj[3])/4
        avL[i]=(avLj[0]+avLj[1]+avLj[2]+avLj[3])/4
        avF[i]=(avFj[0]+avFj[1]+avFj[2]+avFj[3])/4
        V1[i]=(V1j[0]+V1j[1]+V1j[2]+V1j[3])/4
        V2[i]=(V2j[0]+V2j[1]+V2j[2]+V2j[3])/4
        V3[i]=(V3j[0]+V3j[1]+V3j[2]+V3j[3])/4
        V4[i]=(V4j[0]+V4j[1]+V4j[2]+V4j[3])/4
        V5[i]=(V5j[0]+V5j[1]+V5j[2]+V5j[3])/4
        V6[i]=(V6j[0]+V6j[1]+V6j[2]+V6j[3])/4
        i+=1
        
    create_svg('I-table',I)
    create_svg('II-table',II)
    create_svg('III-table',III)
    create_svg('avR-table',avR)
    create_svg('avL-table',avL)
    create_svg('avF-table',avF)
    create_svg('V1-table',V1)
    create_svg('V2-table',V2)
    create_svg('V3-table',V3)
    create_svg('V4-table',V4)
    create_svg('V5-table',V5)
    create_svg('V6-table',V6)
    
    
if __name__ == '__main__':
    main()