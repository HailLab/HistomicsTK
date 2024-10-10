import json
import sys
from PIL import Image, ImageDraw


def load_json(json_file_path):
    with open(json_file_path, 'r') as f:
        return json.load(f)

def draw_polygon(draw, points, fill_color, outline_color):
    flattened_points = [coord for point in points for coord in point[:2]]
    draw.polygon(flattened_points, fill=fill_color, outline=outline_color)

def render_annotations(base_image_path, json_file_path, output_path, quality=92):
    try:
        json_data = load_json(json_file_path)
        base_image = Image.open(base_image_path).convert('RGBA')
    except IOError:
        return False

    # Create a new transparent layer for annotations
    annotation_layer = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(annotation_layer)

    fill_color = (74, 204, 181, 74)
    outline_color = (0, 212, 186, 209)

    # Extract and draw annotations
    annotations = json_data['annotations'][0]['annotation']['elements']
    for annotation in annotations:
        if annotation['type'] == 'polyline' and annotation['closed']:
            draw_polygon(draw, annotation['points'], fill_color, outline_color)

    # Combine base image and annotation layer
    result = Image.alpha_composite(base_image, annotation_layer)

    try:
        result.convert('RGB').save(output_path, 'JPEG', quality=quality, subsampling="4:2:0", progressive=True)
    except IOError:
        return False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <base_image_path> <json_file_path> <output_path>")
        sys.exit(1)

    base_image_path = sys.argv[1]
    json_file_path = sys.argv[2]
    output_path = sys.argv[3]

    render_annotations(base_image_path, json_file_path, output_path)

