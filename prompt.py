BODY_ANNO='''The following is annotation of psd file layers, please identify which of them denote torso of this painting. Some fraquently used annotations are '顔', 'body', '体'.
    
For example:
##
Inputs:顔,目,口,顔のポイント,眉,前髪,横髪,髪型,服,ブラウス,服のパーツ,リボンの頭者,ピアス,✿,髪飾り2,ボンネット,ボンネットちいさめ,空
想パーツ,羽,ブーケ,手,背景,ポイント,まるい,ペット
Output: 顔
##
Inputs: 素体,目,目2,眉毛,鼻,口,前髪,後ろ髪,髪型,メガネ,服,メイク,メイク2,メイク3,手,背景
Output: 素体
##
Inputs: тело,уши,глаза,нос,губы,брови,facepaint,blush,прическа 1,прическа2,пряди,аксессуары,одежда,одежда2,шапки,очки,фоны
Output:тело
##
Inputs: 얼굴,귀,귀걸이,눈,눈썹,입,머리카락,옆머리,뒷머리,장식,옷,배경
Output: 얼굴
##
Inputs: base,eyes,nose,brows,mouth,features-1,features-2,fringe,middle-hair,bangs,ponytail,clothes,outer-clothes,accessories,fantasy,hats,background
Output: base
##
Inputs: {input}
Output: 
'''

ITEM_ADDITION='''You will be presented with two anime-style images. The image on the left represents a {cp_name} component. When this component is applied to a portrait, the outcome is displayed in the image on the right. Your task is to provide a detailed description of the left image, focusing specifically on the {cp_name} component. This detailed description is intended to serve as a clear instruction for an artist to accurately replicate the {cp_name} component as seen in the left image.
'''
ITEM_ADDITION_PART1='''You will be presented with two anime-style images. The following image represents a {cp_name} component denote as the first image:
'''
ITEM_ADDITION_PART2='''When this component is applied to a portrait, the outcome is displayed as the following, denoted as the second image. Your task is to provide a detailed description of the first image, focusing specifically on the {cp_name} component. This description is intended to serve as a clear instruction for an artist to accurately replicate the {cp_name} component as seen in the first image. The instruction should start with "Add a {cp_name} component ...". Don't mention the first image or instruction for artist in the instruction!
'''


ITEM_ANNO='''You will be presented with a pair of images that represent different layers within a PSD file. The image on the left shows the PSD project's appearance when all layers are visible. The image on the right depicts the rendering when only one specific layer is visible. Your task is to:
1. Select a proper name for the specific layer from the provided list of valid names.
2. Ensure that the chosen name accurately reflects the content and purpose of the layer.
Valid Names: {names}
'''

ITEM_ANNO_PART1='''You will be shown images that represent the rendering results of a PSD file. If all layers are visible, the final image will appear as follows:
'''
ITEM_ANNO_PART2='''If we make only this layer visible, the final image will appear as follows. Your task is to:
1. Select a proper name for the specific layer from the provided list of valid names.
2. Ensure that the chosen name accurately reflects the content and purpose of the layer.
Valid Names: {names}
'''


CATEGORY_ANNO='''Following are lay names of many different psd files. Because those files are created by different artist hence a same layer could end up with different names. I want you to merge similar layer names and give it a unique name in English. 

Layer names:
{names}
'''