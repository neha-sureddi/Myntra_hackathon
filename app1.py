from flask import Flask, render_template
import pandas as pd
import ast

app = Flask(__name__)

# Read Myntra product dataset
data = pd.read_csv('data.csv')
df = data[['p_id', 'name', 'colour', 'img', 'ratingCount', 'avg_rating', 'price', 'p_attributes']]
df.rename(columns={'p_id': 'Product_ID', 'name': 'Product_Name'}, inplace=True)
df.dropna(axis=0, how='any', inplace=True)
ndf = df.drop_duplicates(subset=["Product_ID", "Product_Name","img"], keep=False)

@app.route('/')
def top_10():
    # Read color palette suggested by color analysis code
    try:
        with open('color_palette.txt', 'r') as f:
            suggested_palette = [line.strip() for line in f.readlines()]  # Read each line as a color code
    except FileNotFoundError:
        suggested_palette = ['#000080', '#800000']  # Default list if file not found or empty

    # Assuming 'suggested_palette' is a list of color codes

    # Filter products based on suggested color palette
    col = pd.read_csv('color_names.csv')
    col = col[['Name', 'Hex (24 bit)']]
    filcol = col[col['Hex (24 bit)'].isin(suggested_palette)]
    coldata = filcol[['Name']]
    pattern = '|'.join(coldata['Name'])
    filtered_df = ndf[ndf['colour'].str.contains(pattern, case=False, na=False)]

    # Calculate Weighted Score
    filtered_df['WeightedScore'] = (0.7 * filtered_df['avg_rating']) + (0.3 * (filtered_df['ratingCount'] / filtered_df['ratingCount'].max()))

    # Select top 10 products based on Weighted Score
    top_products = filtered_df.sort_values(by='WeightedScore', ascending=False).head(10)

    # Convert top_products to a list of dictionaries
    products = top_products.to_dict(orient='records')

    return render_template('top_10.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    selected_product = df[df['Product_ID'] == product_id].iloc[0]

    # Extract attributes of the selected product
    selected_attributes = ast.literal_eval(selected_product['p_attributes'])
    selected_color = selected_attributes.get('color', '')
    selected_type = selected_attributes.get('type', '')

    # Function to match similar items
    def attributes_match(attributes, color, type_):
        try:
            attributes = ast.literal_eval(attributes)
            return attributes.get('color', '') == color and attributes.get('type', '') == type_
        except (ValueError, SyntaxError):
            return False

    # Filter similar items based on color and type
    similar_items_df = df[df['Product_ID'] != product_id]  # Exclude the selected product itself
    similar_items_df = similar_items_df[similar_items_df['p_attributes'].apply(attributes_match, args=(selected_color, selected_type))]

    # Convert similar_items_df to a list of dictionaries
    similar_items = similar_items_df.to_dict(orient='records')

    return render_template('product_detail.html', product=selected_product, similar_items=similar_items)

if __name__ == '__main__':
    app.run(debug=True)
