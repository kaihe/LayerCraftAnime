import random
import os, json
from Maker import Maker
from common.tools import grid_ims
from PIL import ImageFont
from PIL import ImageDraw 
import matplotlib.pyplot as plt
import math

root = r'D:\picrew\data'
def test():
    f_path = r'data\gpt4o_component_description_batch_result\20240901_f3e6.jsonl'

    ims = []
    instructions = []

    for line in open(f_path).readlines():
        data = json.loads(line.strip())
        pid = data['pid']
        comp_combo = data['cp_combo']

        maker = Maker(os.path.join(root, pid))
        comp_im = maker.render_combo(comp_combo)

        ims.append(comp_im)
        _anno = json.loads(data['description'])
        instructions.append(_anno['Instruction'])
        # details.append('\n'.join([k['detail'] for k in _anno['Description']]))
    

    for im, ins in zip(ims, instructions):
        # i = _i//col_num
        # j = _i%col_num
        # axarr[i,j].imshow(im)
        # axarr[i,j].title.set_text(name)
        # axarr[i,j].axis('off')
        
        # axarr[i,j].text(0, 200, name+'\n\n'+desc, dict(size=10), wrap=True)

        display_image_with_description(im, ins)


def display_image_with_description(image, description):
    # Create a figure and axis
    fig, ax = plt.subplots()
    
    # Display the image
    ax.imshow(image)
    
    # Remove the axis ticks and labels
    ax.axis('off')
    
    # Add the description as a title
    # ax.set_title(description)
    ax.text(0, 200, description, dict(size=10), wrap=True)
    
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    # Show the plot
    plt.show()

if __name__ == '__main__':
    test()