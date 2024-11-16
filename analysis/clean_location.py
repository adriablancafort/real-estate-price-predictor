import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_paths():
    """Setup and return all necessary paths."""
    base_dir = Path.cwd().parent
    modified_dir = base_dir / 'dataset' / 'modified'
    modified_dir.mkdir(exist_ok=True)
    
    return {
        'test': modified_dir / 'test_modified.csv',
        'train': modified_dir / 'train_modified.csv',
        'modified': modified_dir
    }


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process a DataFrame to add missing latitude and longitude data."""
    df = df.copy()
    
    # Create mask for confidential locations (that are fully redacted)
    mask = (df["Location.GIS.Latitude"] == 40.6331249) & (df["Location.GIS.Longitude"] == -89.3985283)
    df.loc[mask, ["Location.GIS.Latitude", "Location.GIS.Longitude"]] = pd.NA

    # Manually fill rows that are not correct
    shelbyville_mask = df["Location.Address.UnparsedAddress"].str.lower() == "407 sw fifth street, shelbyville, il 62565"
    normal_mask = df["Location.Address.UnparsedAddress"].str.lower() == "712 & 715 golfcrest road, normal, il 61761"
    
    # Update coordinates for Shelbyville address
    df.loc[shelbyville_mask, "Location.GIS.Latitude"] = 39.402713789610495
    df.loc[shelbyville_mask, "Location.GIS.Longitude"] = -88.79728330743421
    # Update coordinates for Normal address
    df.loc[normal_mask, "Location.GIS.Latitude"] = 40.529155234759784
    df.loc[normal_mask, "Location.GIS.Longitude"] = -89.00127842461578
    
    return cartesian_to_polar(df)


def cartesian_to_polar(df: pd.DataFrame) -> pd.DataFrame:
    """Convert latitude/longitude to polar coordinates (r, theta)."""
    df = df.copy()
    
    # Convert to radians
    lat_rad = np.radians(df["Location.GIS.Latitude"])
    lon_rad = np.radians(df["Location.GIS.Longitude"])
    
    # Calculate r (distance from origin)
    # Using Earth's radius in kilometers (6371 km)
    R = 6371
    r = R * np.arccos(np.sin(lat_rad) * np.sin(0) + 
                     np.cos(lat_rad) * np.cos(0) * np.cos(lon_rad - 0))
    
    # Calculate theta (angle from reference direction)
    theta = np.arctan2(lon_rad, lat_rad)
    
    # Add new columns
    df["Polar.R"] = r
    df["Polar.Theta"] = np.degrees(theta)  # Convert back to degrees
    
    return df


def main():
    # Setup paths
    paths = setup_paths()
    
    try:
        # Read and process datasets
        logging.info("Processing test dataset...")
        df_test = pd.read_csv(paths['test'], low_memory=False)
        df_test_processed = clean_dataframe(df_test)
        df_test_processed.to_csv(paths['modified'] / 'test_clean.csv', index=False)
        
        logging.info("Processing train dataset...")
        df_train = pd.read_csv(paths['train'], low_memory=False)
        df_train_processed = clean_dataframe(df_train)
        df_train_processed.to_csv(paths['modified'] / 'train_clean.csv', index=False)
        
        logging.info("Modified datasets have been saved successfully.")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()