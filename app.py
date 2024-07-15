from flask import Flask, render_template, request, jsonify, session
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import pandas as pd
import ast
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Skin tone colors with HEX values
indian_skin_tones = {
    "toffee": [123, 70, 56],
    "dark brown": [161, 100, 68],
    "medium": [178, 113, 71],
    "exotic": [205, 142, 99],
    "wheatish": [222, 156, 108],
    "normal": [241, 183, 143],
    "light neutral": [253, 211, 162],
    "fair": [254, 218, 184]
}

# Color palettes for each skin tone
skin_tone_palettes = {
    "toffee": {
        "suitable": ["#50C878", "#4169E1", "#800020", "#FFDB58", "#40E0D0", "#800080", "#CC5500", "#808000", "#FF7F50", "#008080", "#FF66CC", "#36454F", "#FFDAB9", "#000080", "#FFFFF0"],
        "avoid": ["#FFFF33", "#FF6EC7", "#D3D3D3", "#F5F5DC", "#AEC6CF", "#77DD77", "#E6E6FA"]
    },
    "dark brown": {
        "suitable": ["#228B22", "#0047AB", "#8B0000", "#FFD700", "#7FFFD4", "#DDA0DD", "#800000", "#C3B091", "#FA8072", "#FF00FF", "#000080", "#FFFDD0", "#B7410E", "#87CEEB", "#F7E7CE"],
        "avoid": ["#39FF14", "#FFFF00", "#FFD1DC", "#FFDAB9", "#D3D3D3", "#98FB98", "#C0C0C0"]
    },
        "medium": {
        "suitable": ["#FFBF00", "#0000FF", "#DC143C", "#FF8C00", "#00CED1", "#9370DB", "#8B4513", "#808000", "#FF4500", "#008B8B", "#FF69B4", "#483C32", "#FAEBD7", "#000080", "#F5DEB3"],
        "avoid": ["#FFFFE0", "#FF1493", "#FFB6C1", "#F5F5DC", "#E0FFFF", "#00FF7F", "#FFFAFA"]
    },
    "exotic": {
        "suitable": ["#FFD700", "#4682B4", "#B22222", "#FF4500", "#5F9EA0", "#9370DB", "#A0522D", "#8A2BE2", "#FF6347", "#2E8B57", "#C71585", "#D2691E", "#FFF5EE", "#000080", "#FFDEAD"],
        "avoid": ["#FFFF00", "#FF69B4", "#FFC0CB", "#F5F5DC", "#AFEEEE", "#66CDAA", "#FFF0F5"]
    },
    "wheatish": {
        "suitable": ["#FFA500", "#00008B", "#B22222", "#FF8C00", "#4682B4", "#9370DB", "#8B4513", "#6B8E23", "#FF6347", "#2E8B57", "#FF1493", "#696969", "#FAEBD7", "#000080", "#F4A460"],
        "avoid": ["#FFFF00", "#FF69B4", "#FFB6C1", "#F5F5DC", "#00CED1", "#98FB98", "#F0E68C"]
    },
    "normal": {
        "suitable": ["#FFD700", "#0000CD", "#FF4500", "#FF6347", "#5F9EA0", "#9370DB", "#8B4513", "#6B8E23", "#FF1493", "#2E8B57", "#FF00FF", "#4B0082", "#FFF5EE", "#000080", "#FFA07A"],
        "avoid": ["#FFFF00", "#FF69B4", "#FFB6C1", "#F5F5DC", "#AFEEEE", "#66CDAA", "#FFF0F5"]
    },
    "light neutral": {
        "suitable": ["#FF4500", "#1E90FF", "#DC143C", "#FFA500", "#5F9EA0", "#9370DB", "#8B4513", "#556B2F", "#FF6347", "#2E8B57", "#FF1493", "#483D8B", "#FAEBD7", "#000080", "#F5F5DC"],
        "avoid": ["#FFFF00", "#FF69B4", "#FFC0CB", "#F5F5DC", "#00CED1", "#98FB98", "#F0E68C"]
    },
    "fair": {
        "suitable": ["#FFA500", "#0000FF", "#DC143C", "#FF4500", "#4682B4", "#9370DB", "#8B4513", "#6B8E23", "#FF1493", "#2E8B57", "#FF00FF", "#696969", "#FFF5EE", "#000080", "#FFE4C4"],
        "avoid": ["#FFFF00", "#FF69B4", "#FFC0CB", "#F5F5DC", "#AFEEEE", "#66CDAA", "#FFF0F5"]
    }
}

def find_closest_skin_tone(rgb_color):
    lab_skin_tones = {tone: convert_color(sRGBColor(*rgb), LabColor) for tone, rgb in indian_skin_tones.items()}
    lab_color = convert_color(sRGBColor(*rgb_color), LabColor)
    min_delta_e = float('inf')
    closest_tone = None
    for tone, lab_skin_tone in lab_skin_tones.items():
        delta_e = delta_e_cie2000(lab_color, lab_skin_tone)
        if delta_e < min_delta_e:
            min_delta_e = delta_e
            closest_tone = tone
    return closest_tone

@app.route('/')
def main_page():
    return render_template('main.html')

@app.route('/color_analysis')
def color_analysis_page():
    return render_template('color_analysis.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    image = Image.open(file)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return jsonify({'image': image_str})

@app.route('/analyze', methods=['POST'])
def analyze_colors():
    data = request.get_json()
    points = data['points']
    image_str = data['image']
    image = Image.open(BytesIO(base64.b64decode(image_str)))

    pixels = [image.getpixel((x, y)) for x, y in points]

    skin_color = pixels[0][:3]  # first point is skin color
    hair_color = pixels[1][:3]  # second point is hair color
    eye_color = pixels[2][:3]   # third point is eye color

    closest_skin_tone = find_closest_skin_tone(skin_color)
    palette = skin_tone_palettes[closest_skin_tone]
    
        # Perform data analysis
    suggested_palette = palette['suitable']
    col = pd.read_csv('color_names.csv')
    col = col[['Name', 'Hex (24 bit)']]
    filcol = col[col['Hex (24 bit)'].isin(suggested_palette)]
    coldata = filcol[['Name']]
    pattern = '|'.join(coldata['Name'])
    filtered_df = ndf[ndf['colour'].str.contains(pattern, case=False, na=False)]

    filtered_df['WeightedScore'] = (0.7 * filtered_df['avg_rating']) + (0.3 * (filtered_df['ratingCount'] / filtered_df['ratingCount'].max()))

    top_products = filtered_df.sort_values(by='WeightedScore', ascending=False).head(10)

    products = top_products.to_dict(orient='records')

    return jsonify({
        'skin_tone': closest_skin_tone,
        'suitable_colors': palette['suitable'],
        'colors_to_avoid': palette['avoid'],
        'top_products': products
    })

@app.route('/top_10_data', methods=['GET'])
def top_10_data():
    # This endpoint is not needed anymore as data is processed in /analyze
    pass

@app.route('/top_10')
def top_10_page():
    # Assuming top_products is available in the session or some other state management
    top_products = session.get('top_products', [])
    return render_template('top_10.html', top_products=top_products)



@app.route('/product/<int:product_id>')
def product_detail(product_id):
    ndf = pd.read_csv('data.csv')
    product = ndf[ndf['ProductID'] == product_id].iloc[0]
    similar_items = ndf[ndf['colour'] == product['colour']].head(5).to_dict(orient='records')
    return render_template('product_detail.html', product=product, similar_items=similar_items)

if __name__ == '__main__':
    ndf = pd.read_csv('data.csv')
    app.run(debug=True)
