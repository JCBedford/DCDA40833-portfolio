import folium
import pandas as pd
import requests
from urllib.parse import quote

# ============================================================
# CONFIGURATION — Your Mapbox credentials
# ============================================================
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiamJlZGZvcmQiLCJhIjoiY21tazIxcG9tMHZwczJwcHl6aXVxYmEzNiJ9.frXWKIS25QgXwPr0UnU_ZA"
MAPBOX_USERNAME = "jbedford"
MAPBOX_STYLE_ID = "cmmb3sj1j007g01ry5j39atoi"

# ============================================================
# MAPBOX TILE URL — Loads your custom Ghibli basemap
# ============================================================
TILE_URL = (
    f"https://api.mapbox.com/styles/v1/{MAPBOX_USERNAME}/{MAPBOX_STYLE_ID}"
    f"/tiles/256/{{z}}/{{x}}/{{y}}@2x?access_token={MAPBOX_ACCESS_TOKEN}"
)

# ============================================================
# MARKER COLORS — One color per location type
# ============================================================
TYPE_COLORS = {
    "Restaurant": "orange",
    "Park":       "green",
    "School":     "blue",
    "Cultural":   "purple",
    "Recreation": "cadetblue",
    "Shopping":   "pink",
    "Worship":    "beige",
    "Historical": "darkred",
}

# ============================================================
# MARKER ICONS — One icon per location type (Font Awesome)
# ============================================================
TYPE_ICONS = {
    "Restaurant": "cutlery",
    "Park":       "tree",
    "School":     "graduation-cap",
    "Cultural":   "university",
    "Recreation": "flag",
    "Shopping":   "shopping-bag",
    "Worship":    "home",
    "Historical": "landmark",
}

# ============================================================
# GEOCODING FUNCTION
# Converts a street address to (latitude, longitude)
# using the Mapbox Geocoding API
# ============================================================
def geocode_address(address):
    encoded = quote(address)
    url = (
        f"https://api.mapbox.com/search/geocode/v6/forward"
        f"?q={encoded}&access_token={MAPBOX_ACCESS_TOKEN}"
    )
    response = requests.get(url)
    data = response.json()

    try:
        coords = data["features"][0]["geometry"]["coordinates"]
        # Mapbox returns [longitude, latitude] — we flip to [lat, lng]
        return coords[1], coords[0]
    except (KeyError, IndexError):
        print(f"  Could not geocode: {address}")
        return None, None

# ============================================================
# POPUP BUILDER
# Creates a styled HTML popup with image, name, type, description
# ============================================================
def build_popup(name, location_type, description, image_url):
    color = TYPE_COLORS.get(location_type, "gray")

    html = f"""
    <div style="
        font-family: Georgia, serif;
        width: 260px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    ">
        <img src="{image_url}"
             onerror="this.src='https://via.placeholder.com/260x140?text=No+Image'"
             style="width:100%; height:140px; object-fit:cover;" />
        <div style="padding: 10px 12px; background: #f9f5ec;">
            <h3 style="margin:0 0 4px 0; color:#2C2C2C; font-size:15px;">{name}</h3>
            <span style="
                background:{color};
                color:white;
                font-size:10px;
                padding:2px 7px;
                border-radius:10px;
                font-family:sans-serif;
            ">{location_type}</span>
            <p style="margin:8px 0 0 0; font-size:12px; color:#4a4a4a; line-height:1.5;">
                {description}
            </p>
        </div>
    </div>
    """
    return folium.Popup(folium.IFrame(html, width=280, height=300), max_width=280)

# ============================================================
# MAIN SCRIPT
# ============================================================
def main():
    # --- Load CSV ---
    print("Loading hometown_locations.csv...")
    df = pd.read_csv("hometown_locations.csv")
    print(f"   Found {len(df)} locations.\n")

    # --- Geocode all addresses ---
    print("Geocoding addresses...")
    lats, lngs = [], []
    for _, row in df.iterrows():
        print(f"   Geocoding: {row['Name']}...")
        lat, lng = geocode_address(row["Address"])
        lats.append(lat)
        lngs.append(lng)

    df["Latitude"] = lats
    df["Longitude"] = lngs

    # Drop any rows that failed to geocode
    df = df.dropna(subset=["Latitude", "Longitude"])
    print(f"\nSuccessfully geocoded {len(df)} locations.\n")

    # --- Create Folium map centered on DeSoto, TX ---
    print("Building map...")
    m = folium.Map(
        location=[32.5896, -96.8572],  # DeSoto, TX center
        zoom_start=13,
        tiles=TILE_URL,
        attr="© Mapbox © OpenStreetMap | Studio Ghibli Style by jbedford"
    )

    # --- Add markers for each location ---
    for _, row in df.iterrows():
        loc_type = row["Type"]
        color = TYPE_COLORS.get(loc_type, "gray")
        icon  = TYPE_ICONS.get(loc_type, "info-sign")

        popup = build_popup(
            name=row["Name"],
            location_type=loc_type,
            description=row["Description"],
            image_url=row["Image_URL"]
        )

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=popup,
            tooltip=row["Name"],  # Shows name on hover
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)

    # --- Add a legend ---
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px; left: 30px;
        background: #f9f5ec;
        border: 2px solid #8B7355;
        border-radius: 10px;
        padding: 12px 16px;
        font-family: Georgia, serif;
        font-size: 13px;
        z-index: 1000;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    ">
        <b style="font-size:14px;">DeSoto, TX</b><br>
        <i style="font-size:11px; color:#666;">Studio Ghibli Hometown Map</i>
        <hr style="border-color:#8B7355; margin:6px 0;">
        <span style="color:orange;">&#9679;</span> Restaurant<br>
        <span style="color:green;">&#9679;</span> Park<br>
        <span style="color:blue;">&#9679;</span> School<br>
        <span style="color:purple;">&#9679;</span> Cultural<br>
        <span style="color:cadetblue;">&#9679;</span> Recreation<br>
        <span style="color:hotpink;">&#9679;</span> Shopping<br>
        <span style="color:#a0896b;">&#9679;</span> Worship<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # --- Save the map ---
    output_file = "desoto_ghibli_map.html"
    m.save(output_file)
    print(f"Map saved as '{output_file}'")
    print("Open it in your browser to view your Ghibli-themed DeSoto map!")

if __name__ == "__main__":
    main()