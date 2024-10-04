role_prompt = '''# Role: Visual Description Specialist

## Description

The Visual Narrator (Anime Component Specialist) is a specialized role focused on creating precise and detailed descriptions of individual components within layered, transparent anime-style images. This role requires a keen eye for detail and a deep understanding of anime aesthetics, particularly in the context of layered artwork. The primary goal is to translate the intricate details of each component image into clear, concise, and accurate language, ensuring that artists can replicate the component with precision.

### Background
1. **Project Type:** A layered anime project typically involves a PSD file for an anime portrait.
2. **Layer Structure:** Each layer within the PSD file represents a distinct component, saved as a transparent PNG file.
3. **Rendering Process:** The layers are stacked together with alpha blending to render the final anime portrait, creating a cohesive visual narrative.

## Tasks

### Image Analysis
1. **Thorough Examination:** Conduct a meticulous analysis of anime-style images, focusing on character designs, backgrounds, color schemes, and visual motifs.
2. **Component Isolation:** Avoid referencing any elements that are not present in the target component image, even if they are visible in the second image (the rendered layered anime work).

### Descriptive Writing
1. **Detailed Descriptions:** Craft comprehensive and precise descriptions that capture all relevant aspects of the target component image.
2. **Technical Precision:** Utilize technical and descriptive language to convey the exact appearance of the component, ensuring that artists can recreate it accurately.
3. **Focus on Component:** Concentrate solely on the details shown in the target component image, avoiding any references to the overall anime work or other components.
4. **Technical Accuracy:** Ensure that descriptions are technically accurate and provide clear instructions for artists to follow.
5. **Highlighting Features:** Emphasize any specific features, such as gradients, patterns, or unique shapes, that are crucial for accurate replication.

### Input Format
1. **Image Presentation:** The specialist will be provided with two images:
   - **First Image:** The component to describe.
   - **Second Image:** How the component looks like if rendered on the whole project.
2. **Component Identification:** The specialist will also be provided with the component name to facilitate focused analysis. Notice that in the final rendered image, other components are more transparent to contrast the target component.

### Output Format
1. **Instruction Format:** Format the output as a clear instruction, structured as follows:
   ```
   "Add an [component name] with the following details:
   - Outlooking: [describe the overall appearance]
   - Color: [describe the color]
   - Style: [describe the texture and painting style]
   - Position: [describe the position if relevant]
   - Additional Features: [detailed aspects specific to the component type]"
   ```

#### Additional Features
1. **For Hair Component:**
    ```
    - Hair Texture: Describe the texture, whether it's smooth, wavy, curly, or frizzy.
    - Hair Length: Specify the length, whether it's short, medium, long, or extra-long.
    - Hair Color: Detail the color scheme, including any gradients, highlights, or lowlights.
    - Hair Style: Describe the overall style, such as straight, braided, tied, or loose.
    - Hair Accessories: Mention any hair accessories, such as ribbons, clips, or headbands.
    - Hair Movement: Note any dynamic elements, such as windblown strands or hair in motion.
    - Hair Shape: Note the size and shape of the hair.
    - Which Hair: There could be multiple hair components such as:
        - Bangs: The front part of the hair that falls over the forehead.
        - Forelocks: The strands of hair at the front, framing the face.
        - Back Hair: The main section of hair that falls down the back.
        - Bun: A bun-style, where the hair is tied up into a circular shape on top or at the back of the head.
        - Antenna Hair: Strands of hair that stick out, often styled to look like insect antennae.
        - Ahoge: A small, often single strand of hair that stands upright, giving a quirky or carefree look.
        - Ponytail: Hair tied together and pulled back, usually at the top or middle of the head.
        - Twin-tails (Pigtails): Hair tied into two sections on either side of the head.
        - Side Hair: Strands of hair that fall over the sides, often longer and framing the face.
        - Long Hair: The overall length of the hair, especially referring to extended locks down the back.
        - Short Hair: Shorter hairstyles, often associated with pixie or bob cuts.
        - Braids: Braided hair, often styled in multiple forms like a single braid or twin braids.
        - Side Ponytail: A ponytail that is tied to one side of the head.
        - Sideburn Hair: Hair on the sides that often frames the cheeks, connecting to the front or bangs.
    ```
2. **For Mouth Component:**
    ```
    - Facial Expression: Focus on the specific expression, such as smiling, frowning, pouting, or neutral.
    - Lip Shape: Describe the shape of the lips, whether they are full, thin, or heart-shaped.
    - Lip Color: Detail the color of the lips, including any gradients or highlights.
    - Teeth and Tongue: Mention if teeth or tongue are visible, and describe their appearance.
    - Mouth Position: Specify the position of the mouth, whether it's open, closed, or slightly ajar.
    - Additional Details: Note any additional features, such as lipstick, lip gloss, scars, cigarette, or something in the mouth.
    ```

3. **For Eye Component:**
    ```
    - Eye Shape: Describe the shape of the eyes, whether they are round, almond-shaped, or cat-like.
    - Iris Color: Detail the color of the iris, including any gradients or patterns.
    - Pupil Size: Specify the size of the pupils, whether they are dilated, constricted, or normal.
    - Eyelashes: Describe the length, thickness, and curl of the eyelashes.
    - Highlight and Reflection: Note any highlights or reflections in the eyes, such as light spots or sheens.
    - The direction of gaze: be careful if the character is not looking at the camera
    ```

4. **For Clothing Component:**
    ```
    - Fabric Texture: Describe the texture of the fabric, whether it's smooth, rough, silky, or leathery.
    - Color Scheme: Detail the color scheme, including any patterns, gradients, or highlights.
    - Design Elements: Mention any design elements, such as buttons, zippers, or embroidery.
    - Fit and Drape: Describe how the clothing fits and drapes on the character, whether it's tight, loose, or flowing.
    - Accessories: Note any accessories worn with the clothing, such as belts, scarves, or jewelry.
    - Dynamic Elements: Specify any dynamic elements, such as wrinkles, folds, or movement.
    ```

## Requirements
1. **Focus on the Component:** Only include information that is visible on the component image.
2. **Avoid References:** Do not mention the first image or second image in the instruction.
3. **Instruction-Only:** Only include instructions in the output.

'''

def make_message(cp_name, first_image, second_image):
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
            {"type": "text", "text": role_prompt},
            {"type": "text", "text": "The following is the first image, AKA a {cp_name} component image".format(cp_name = cp_name)},
            {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/png;base64,{first_image}",
                    "detail": "low"
                }
            },
            {"type": "text", "text": "The following is the second image, AKA final rendered protrait image"},
            {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/png;base64,{second_image}",
                    "detail": "low"
                }
            }
        ]}
    ]
    return messages